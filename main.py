from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
SHOULD_UPDATE = bool(os.environ.get("SHOULD_UPDATE") == 'True')

print(f"SHOULD_UPDATE: {SHOULD_UPDATE}")

CLOUDFLARE_AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"
}


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    records: List[DNSRecord]

    def __str__(self):
        return f"{self.id} {self.name}"

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "records": [record.to_json() for record in self.records]
        }

    def get(self, param):
        return getattr(self, param)


@dataclass(frozen=True)
class DNSRecord:
    id: str
    zone_id: str
    zone_name: str
    name: str
    type: str
    content: str
    proxiable: bool
    proxied: bool
    ttl: int
    settings: dict
    meta: dict
    comment: str
    tags: List[str]
    created_on: str
    modified_on: str
    comment_modified_on: str

    def __str__(self):
        return f"{self.id} {self.name} {self.type} {self.content}"

    def to_json(self):
        return {
            "id": self.id,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "name": self.name,
            "type": self.type,
            "content": self.content,
            "proxiable": self.proxiable,
            "proxied": self.proxied,
            "ttl": self.ttl,
            "settings": self.settings,
            "meta": self.meta,
            "comment": self.comment,
            "tags": self.tags,
            "created_on": self.created_on,
            "modified_on": self.modified_on,
            "comment_modified_on": self.comment_modified_on
        }


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip_address = response.json().get('ip')

        logging.info(f"public IP address is: {ip_address}")

        return ip_address
    except requests.RequestException as e:
        logging.error(f"Error fetching IP address: {e}")
        return None


def get_dns_by_zone_id() -> List[Zone]:
    if not os.path.exists("data/zones.json"):
        logging.error("data/zones.json file not found.")
        return []

    with open("data/zones.json", "r") as file:
        zones = json.load(file)

    for zone in zones:
        records = get_dns_records(zone.get('id'), zone.get('name'))
        zone['records'] = records.records

    return zones


def get_dns_records(zone_id: str, domain: str) -> Zone:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

    response = requests.request("GET", url, headers=CLOUDFLARE_AUTH_HEADERS)

    records = []
    if response.status_code == 200:
        data = response.json().get('result')
        for record in data:
            records.append(DNSRecord(**record))
    else:
        logging.error(f"Error fetching DNS records: {response.text}")

    zone = Zone(id=zone_id, name=domain, records=records)

    os.makedirs(f"data/{domain}", exist_ok=True)
    with open(f"data/{domain}/fetched_records.json", "w") as file:
        json.dump(zone.to_json(), file, indent=4)

    return zone


class RecordTypeNotSupportedError:
    pass


def ip_address_differs(record: DNSRecord, ip_address: str) -> bool | RecordTypeNotSupportedError:
    if record.type == "A" and record.content == ip_address:
        logging.info(f"IP address for {record.name} is the same as the public IP address.")
        return False
    if record.type == "A" and record.content != ip_address:
        logging.info(f"IP address for {record.name} is different from the public IP address.")
        logging.info(f"Record ip: {record.content} - Public ip: {ip_address}")
        return True
    logging.info(f"Record type {record.type} is not supported.")
    return RecordTypeNotSupportedError()


def update_dns_record(record: DNSRecord, ip_address: str) -> None:
    url = f"https://api.cloudflare.com/client/v4/zones/{record.zone_id}/dns_records/{record.id}"

    comment = f"Updated by Cloudflare API with IP address {ip_address}, old IP address was {record.content}"

    payload = {
        "comment": comment,
        "name": record.name,
        "proxied": record.proxied,
        "settings": record.settings,
        "tags": record.tags,
        "ttl": record.ttl,
        "content": ip_address,
        "type": record.type
    }

    response = requests.request("PUT", url, json=payload, headers=CLOUDFLARE_AUTH_HEADERS)
    data = response.json()['result']

    logging.info(f"Record {data['name']} updated successfully with IP address {data['content']}.")

def run():
    ip_address = get_public_ip()
    zones = get_dns_by_zone_id()

    for zone in zones:
        for record in zone.get('records'):
            differs = ip_address_differs(record, ip_address)
            if differs and not isinstance(differs, RecordTypeNotSupportedError) and SHOULD_UPDATE:
                logging.info(f"Updating DNS record for {record.name}")
                update_dns_record(record, ip_address)

if __name__ == "__main__":
    run()