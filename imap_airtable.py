# airtable_manager.py

# Assuming logger_config is in a shared utils folder
# from Shared.Utils.logger_config import setup_logger
# logger = setup_logger(__name__)
# For standalone testing, using a basic logger:
import logging
import os
from datetime import datetime

import pytz
import requests
from dotenv import load_dotenv
from pyairtable import Api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Load dotenv from project root ---
# Assumes .env file is in the same directory or a parent directory
load_dotenv()


class AirtableClient:
    def __init__(self, table_key: str = None):
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing AIRTABLE_API_KEY in environment variables")

        self.api = Api(self.api_key)

        # These will be set by the fetch methods
        self.base_id = None
        self.table_id = None
        self.view_name = None

        if table_key:
            # This logic remains for other uses
            table_map = {
                "warmup_accounts": {
                    "base_id": os.getenv("IG_ARMY_BASE_ID"),
                    "table_id": os.getenv("IG_ARMY_WARMUP_ACCOUNTS_TABLE_ID"),
                    "view": "Warmup",
                },
                # Add other table keys here if needed
            }
            if table_key in table_map:
                config = table_map[table_key]
                self.base_id = config["base_id"]
                self.table_id = config["table_id"]
                self.view_name = config["view"]
                if not all([self.base_id, self.table_id, self.view_name]):
                    raise ValueError(
                        f"Missing required environment variables for table key: '{table_key}'"
                    )
            else:
                raise ValueError(f"Unsupported table key: '{table_key}'")

    def update_record_fields(self, record_id: str, fields: dict):
        """
        Update arbitrary fields in an Airtable record.
        Requires self.base_id and self.table_id to be set.
        """
        if not all([self.base_id, self.table_id]):
            raise ValueError(
                "Base ID and Table ID must be set before updating records. Call a fetch method first."
            )
        try:
            table = self.api.table(self.base_id, self.table_id)
            result = table.update(record_id, fields, typecast=True)
            logger.info(f"✅ Updated record {record_id} with fields: {fields}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to update record {record_id}: {e}")
            return None

    # --- NEW FUNCTION ---
    def get_imap_accounts(self, max_records: int = 1) -> list:
        """
        Fetches account credentials from the 'IMAP' view where 'IMAP Status' is 'Off'.

        Args:
            max_records (int): The maximum number of accounts to fetch. Defaults to 1.

        Returns:
            list: A list of dictionaries, each containing the credentials for one account.
                  Returns an empty list if no accounts are found or an error occurs.
        """
        try:
            # Set the instance variables for base and table ID for this operation
            self.base_id = os.getenv("IG_ARMY_BASE_ID")
            self.table_id = os.getenv(
                "IG_ARMY_ACCS_TABLE_ID"
            )  # Assuming same table as unused accounts
            self.view_name = "IMAP"

            if not all([self.base_id, self.table_id]):
                raise ValueError(
                    "Missing IG_ARMY_BASE_ID or IG_ARMY_ACCS_TABLE_ID in .env file"
                )

            logger.info(
                f"📡 Fetching up to {max_records} accounts from view '{self.view_name}'..."
            )
            logger.info(f"   Base: {self.base_id}, Table: {self.table_id}")

            table = self.api.table(self.base_id, self.table_id)
            fields_to_fetch = ["Email", "Email Password", "IMAP Status"]

            # Formula to only fetch records where 'IMAP Status' is 'Off'
            formula = "({IMAP Status} = 'Off')"

            records = table.all(
                view=self.view_name,
                fields=fields_to_fetch,
                formula=formula,
                max_records=max_records,
            )

            if not records:
                logger.warning(
                    f"⚠️ No accounts with 'IMAP Status' = 'Off' found in the '{self.view_name}' view."
                )
                return []

            accounts_list = []
            for record in records:
                record_fields = record.get("fields", {})

                email_address = record_fields.get("Email")
                email_password = record_fields.get("Email Password")

                if not all([email_address, email_password]):
                    logger.warning(
                        f"Skipping record {record.get('id')} due to missing credentials."
                    )
                    continue

                accounts_list.append(
                    {
                        "record_id": record.get("id"),
                        "email": email_address,  # Key named to match activate_email_protocols
                        "password": email_password,  # Key named to match activate_email_protocols
                    }
                )

            logger.info(
                f"✅ Successfully fetched credentials for {len(accounts_list)} accounts."
            )
            return accounts_list

        except Exception as e:
            logger.error(
                f"❌ An error occurred while fetching IMAP accounts: {e}",
                exc_info=True,
            )
            return []
