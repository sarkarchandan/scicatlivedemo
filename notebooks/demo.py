"""
demo.py
-------
"""
from datetime import datetime
import json
from typing import Dict
import requests


class SciCatHandler:

    _token: str
    _secrets: str = ".secrets"
    _base_url: str = "http://backend.localhost/api/v3"

    def __init__(self):
        self._fetch_token()

    def _fetch_token(self) -> None:
        with open(file=self._secrets, mode="r") as sf:
            auths = sf.readlines()
            user = auths[0].rstrip().split("=")[1]
            password = auths[1].rstrip().split("=")[1]
            endpoint = self._base_url +  "/auth/login"
            response = requests.post(
                endpoint,
                json={"username": user, "password": password},
                headers={}, stream=False, verify=True)
            if not response.ok:
                try:
                    response_text = response.json()
                except json.decoder.JSONDecodeError:
                    response_text = response.text
                    raise RuntimeError(f"auth failure: {response_text}")
            print(f"Auth token fetched from {self._base_url}.")
            self._token = response.json()["id"]

    @property
    def _header(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}


class ProposalHandler(SciCatHandler):

    _proposal: str = "proposal.json"

    def __init__(self):
        super().__init__()

    def get_dummy_proposal(self) -> Dict[str, str]:
        with open(file="proposal.json", mode="r") as fp:
            return json.load(fp=fp)

    def register(self, proposal: Dict[str, str]) -> None:
        endpoint = self._base_url +  "/proposals"
        response = requests.post(
            url=endpoint,
            headers=self._header,
            json=proposal
        )
        if response.status_code != 201:
            print(f"Could not register proposal, {response.json()}")
            return None
        print(f"Proposal is registered with Id: {response.json()['proposalId']}")


class AcquisitionHandler(SciCatHandler):

    _proposal: Dict[str, str]
    _dataset_type: str = "raw"

    def __init__(self):
        super().__init__()

    def fetch_proposal(self, proposal_id: str) -> None:
        endpoint = self._base_url +  "/proposals/" + proposal_id
        response = requests.get(
            url=endpoint,
            headers=self._header
        )
        if response.status_code != 200:
            print(f"Could not fetch proposal, {response.json()}")
            return
        self._proposal = response.json()
        print(f"Fetched Proposal: {self._proposal}")
        print(f"Number of samples = {len(self._proposal['metadata']['samples'])}")

    def handle_acquisitions(self) -> None:
        endpoint = self._base_url + "/datasets"
        with open(file="metadata.json", mode="r") as fp:
            metadata = json.load(fp=fp)
        for acq in self._proposal["metadata"]["samples"]:
            sample_name = acq["specimen_name"]
            sample_code = acq["qr_code_label"]
            payload = {
                "pid": f"{self._proposal['proposalId']}_{sample_code}",
                "type": self._dataset_type,
                "ownerGroup": self._proposal["ownerGroup"],
                "accessGroups": self._proposal["accessGroups"],
                "principalInvestigator": f"{self._proposal['pi_firstname']} {self._proposal['pi_lastname']}",
                "owner": f"{self._proposal['firstname']} {self._proposal['lastname']}",
                "ownerEmail": self._proposal["email"],
                "contactEmail": self._proposal["pi_email"],
                "sourceFolder": "/mnt/ips-mnt-01/smart-morph",
                "sourceFolderHost": "ips-mnt-01.ips.kit.edu",
                "numberOfFiles": 3,
                "creationTime": datetime.today().isoformat(),
                "keywords": ["entomology", "biology", "insects", "museums"],
                "description": f"Serial-MicroCT of {sample_name}",
                "datasetName": sample_name,
                "scientificMetadata": metadata,
                "dataQualityMetrics": 0,
                "startTime": datetime.today().isoformat(),
                "endTime": datetime.today().isoformat(),
                "creationLocation": "Deutsches Elektronen-Synchrotron DESY / PETRA III / P23 / HIKA",
                "proposalId": self._proposal["proposalId"],
                "usedSoftware": ["Concert", "Ufo-Tofu"]
            }
            response = requests.post(
                url=endpoint,
                headers=self._header,
                json=payload
            )
            if response.status_code != 201:
                print(f"Could not handle acquisition for {sample_name}: {response.json()}")
            else:
                print(f"Handled acquisition for {sample_name}")


if __name__ == "__main__":
    pass
