"""
ISO 8583 Mastercard Field 48 (DE48) Parser
Additional Data - Private Use

Subelement format: [2-digit ID][3-digit length][value]
"""

from dataclasses import dataclass, field
from typing import Optional


# Mastercard DE48 Subelement definitions: (name, description)
DE48_SUBELEMENTS = {
    "01": ("Transit/Transportation", "Transit system transaction data"),
    "02": ("Auth Indication", "Authorization indicator"),
    "03": ("Loyalty Data", "Loyalty program data"),
    "04": ("Mastercard Fraud Scoring", "Fraud scoring data"),
    "05": ("AUCL Data", "Account update data"),
    "07": ("MCCS Data", "Mastercard Custom Payment Service"),
    "08": ("Merchant Advice", "Merchant advice code"),
    "10": ("CVV2", "Card Verification Value 2"),
    "11": ("Forwarding Institution ID", "Forwarding institution identifier"),
    "12": ("Acquirer Reference", "Acquirer reference data"),
    "14": ("Commercial Card", "Commercial card data"),
    "18": ("Service Code", "Service code data"),
    "20": ("Cardholder Verification", "Cardholder verification data"),
    "21": ("Merchant Verification Value", "MVV data"),
    "22": ("Multi-Purpose Merchant Indicator", "MPMI data"),
    "23": ("Payment Initiation Channel", "Channel indicator"),
    "24": ("Mastercard Assigned ID", "MID assigned by Mastercard"),
    "25": ("Account Status Inquiry", "ASI data"),
    "26": ("Wallet Program Data", "Digital wallet data"),
    "32": ("Mastercard Assigned ID", "Mastercard assigned identifier"),
    "33": ("PAN Mapping Info", "PAN mapping file information"),
    "37": ("Additional Merchant Data", "Extended merchant data"),
    "38": ("E-Commerce Indicators", "Electronic commerce indicators"),
    "39": ("Account Number Mapping", "Account number mapping"),
    "40": ("Account Mapping Result", "Account number mapping result"),
    "41": ("Token Transaction ID", "Token transaction identifier"),
    "42": ("E-Commerce Security Level", "Security level indicator and UCAF"),
    "43": ("UCAF", "Universal Cardholder Authentication Field"),
    "44": ("Device Type Indicator", "Device type indicator"),
    "45": ("POS Card Level Results", "POS card level results"),
    "48": ("Security Protocols", "Security protocol data"),
    "49": ("Electronic Commerce", "E-commerce data"),
    "50": ("Cryptocurrency Indicator", "Cryptocurrency transaction indicator"),
    "54": ("Commercial Data", "Commercial transaction data"),
    "55": ("Merchant Fraud Advice", "Fraud advice data"),
    "57": ("Network Indicators", "Network processing indicators"),
    "58": ("Issuer Fraud Report", "Fraud report data"),
    "59": ("Transaction Processing", "Transaction processing indicators"),
    "60": ("Advice Reason Code", "Reason code for advice"),
    "61": ("POS Data", "Point of sale data"),
    "62": ("Custom Payment Service", "CPS data"),
    "63": ("Trace ID", "Trace identifier"),
    "64": ("Transit Data", "Transit transaction data"),
    "65": ("MDES Token Cryptogram", "Token cryptogram data"),
    "66": ("Funding/Disbursement", "Funding transaction details"),
    "67": ("Transit Gateway Data", "Transit gateway data"),
    "68": ("Account Level Management", "ALM data"),
    "70": ("Contactless Cryptogram", "Contactless cryptogram data"),
    "71": ("On-Behalf Services", "OBS data"),
    "72": ("MasterPass Data", "Value added services data"),
    "73": ("Additional Transaction Data", "Additional transaction data"),
    "74": ("Merchant Advice Code", "Merchant advice code"),
    "75": ("Address Verification", "AVS data"),
    "76": ("Key Exchange Data", "Key exchange/derivation data"),
    "77": ("Payment Service Indicators", "PSI data"),
    "78": ("Commercial Card Data", "Commercial card data"),
    "79": ("Issuer Chip Auth", "Issuer chip authentication"),
    "80": ("Contactless Data", "Contactless transaction data"),
    "82": ("ALM Inquiry", "Account level management inquiry"),
    "83": ("ALM Response", "Account level management response"),
    "84": ("Transaction Category", "Transaction category code"),
    "86": ("E-Commerce Merchant Data", "E-commerce merchant/acquirer referral"),
    "87": ("Acquirer Reference Data", "Acquirer reference data"),
    "88": ("Auth Characteristics", "Authorization characteristics indicator"),
    "89": ("Card Level Results", "Card level results"),
    "90": ("Transaction Identifier", "Transaction identifier"),
    "92": ("CVC2 Result", "CVC2 verification result"),
    "95": ("Replacement Amounts", "Replacement amount data"),
    "96": ("Authorization Method", "Authorization method indicator"),
    "98": ("Terminal Output", "Terminal output data"),
    "99": ("Transaction Characteristics", "Transaction characteristics"),
}

# SE22 - Multi-Purpose Merchant Indicator sub-fields
SE22_FIELDS = {
    0: ("Merchant Type", 1),       # pos 0, len 1
    1: ("Installment Payment", 1), # pos 1, len 1
    2: ("Bill Payment", 1),        # pos 2, len 1
    3: ("Recurring Payment", 1),   # pos 3, len 1
    4: ("Lodging Check-in", 1),    # pos 4, len 1
    5: ("Lodging Check-out", 1),   # pos 5, len 1
    6: ("TimePeriod", 4),          # pos 6-9, len 4
    10: ("Number of Installments", 2),  # pos 10-11
    12: ("Installment Sequence", 2),    # pos 12-13
}

# SE61 - POS Data sub-fields (fixed positions)
SE61_FIELDS = {
    0:  ("Terminal Attended", 1),
    1:  ("PSAM Present", 1),
    2:  ("Security Condition", 1),
    3:  ("Cardholder Activated Terminal Level", 1),
    4:  ("Card Data Input Mode", 1),
    5:  ("Cardholder Auth Method", 1),
    6:  ("Cardholder Auth Entity", 1),
    7:  ("Card Data Output Capability", 1),
    8:  ("Terminal Output Capability", 1),
    9:  ("PIN Capture Capability", 1),
    10: ("Operative Environment", 1),
    11: ("Reserved", 1),
}

# SE43 - UCAF sub-fields
SE43_FIELDS = {
    0: ("UCAF Collection Indicator", 1),
    1: ("UCAF Data", -1),  # variable length, rest of field
}

# SE38 - E-Commerce Indicators sub-fields
SE38_FIELDS = {
    0: ("Electronic Commerce Indicator", 2),
    2: ("CAVV", 20),
    22: ("CAVV Algorithm", 1),
    23: ("XID", 20),
    43: ("DS Transaction ID", 36),
}


@dataclass
class Subelement:
    id: str
    length: int
    value: str
    name: str = ""
    description: str = ""
    parsed_fields: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.id in DE48_SUBELEMENTS:
            self.name, self.description = DE48_SUBELEMENTS[self.id]

    def display(self, verbose: bool = False) -> str:
        label = f"SE{self.id}"
        if self.name:
            label += f" ({self.name})"
        lines = [f"  {label}: [{self.length:03d}] {self.value!r}"]
        if verbose and self.parsed_fields:
            for k, v in self.parsed_fields.items():
                lines.append(f"      {k}: {v!r}")
        return "\n".join(lines)


@dataclass
class DE48ParseResult:
    raw: str
    subelements: list
    errors: list = field(default_factory=list)

    def get(self, se_id: str) -> Optional[Subelement]:
        for se in self.subelements:
            if se.id == se_id:
                return se
        return None

    def __str__(self) -> str:
        lines = [f"DE48 Parse Result (raw length: {len(self.raw)})"]
        lines.append(f"  Subelements found: {len(self.subelements)}")
        for se in self.subelements:
            lines.append(se.display(verbose=True))
        if self.errors:
            lines.append("  Errors:")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


def _parse_se22(value: str) -> dict:
    """Parse SE22 Multi-Purpose Merchant Indicator sub-fields."""
    parsed = {}
    if len(value) >= 1:
        codes = {
            "0": "Not Used",
            "1": "Installment Payment",
            "2": "Debt Repayment",
            "3": "Deferred Payment",
        }
        parsed["Merchant Type"] = codes.get(value[0], value[0])
    if len(value) >= 2:
        ind = {"0": "No", "1": "Yes", "2": "Pre-Auth", "9": "Not Applicable"}
        parsed["Installment Payment"] = ind.get(value[1], value[1])
    if len(value) >= 3:
        ind = {"0": "No", "1": "Yes", "9": "Not Applicable"}
        parsed["Bill Payment"] = ind.get(value[2], value[2])
    if len(value) >= 4:
        ind = {"0": "No", "1": "Yes", "9": "Not Applicable"}
        parsed["Recurring Payment"] = ind.get(value[3], value[3])
    if len(value) >= 5:
        ind = {"0": "No", "1": "Yes", "9": "Not Applicable"}
        parsed["Lodging Check-in"] = ind.get(value[4], value[4])
    if len(value) >= 6:
        ind = {"0": "No", "1": "Yes", "9": "Not Applicable"}
        parsed["Lodging Check-out"] = ind.get(value[5], value[5])
    if len(value) >= 10:
        parsed["Time Period (MMYY)"] = value[6:10]
    if len(value) >= 12:
        parsed["Number of Installments"] = value[10:12]
    if len(value) >= 14:
        parsed["Installment Sequence"] = value[12:14]
    return parsed


def _parse_se38(value: str) -> dict:
    """Parse SE38 E-Commerce Indicators."""
    parsed = {}
    if len(value) >= 2:
        eci_map = {
            "00": "Not a UCAF transaction",
            "01": "Merchant-only UCAF",
            "02": "Fully authenticated UCAF",
            "05": "Visa ECI - fully authenticated",
            "06": "Visa ECI - attempted",
            "07": "Visa ECI - not authenticated",
        }
        eci = value[0:2]
        parsed["ECI"] = eci_map.get(eci, eci)
    if len(value) >= 22:
        parsed["CAVV"] = value[2:22]
    if len(value) >= 23:
        alg_map = {"0": "CVV", "1": "HMAC", "2": "CVV2", "3": "MasterCard AAV"}
        alg = value[22]
        parsed["CAVV Algorithm"] = alg_map.get(alg, alg)
    if len(value) >= 43:
        parsed["XID"] = value[23:43]
    if len(value) >= 79:
        parsed["DS Transaction ID"] = value[43:79]
    return parsed


def _parse_se43(value: str) -> dict:
    """Parse SE43 Universal Cardholder Authentication Field."""
    parsed = {}
    if len(value) >= 1:
        ind_map = {
            "0": "UCAF data collection not supported",
            "1": "UCAF data collection supported, not populated",
            "2": "UCAF data collection supported, data populated by cardholder",
        }
        parsed["Collection Indicator"] = ind_map.get(value[0], value[0])
    if len(value) > 1:
        parsed["UCAF Data"] = value[1:]
    return parsed


def _parse_se61(value: str) -> dict:
    """Parse SE61 POS Data."""
    parsed = {}
    if len(value) >= 1:
        term_map = {"1": "Attended", "2": "Unattended", "9": "Not Applicable"}
        parsed["Terminal Attended"] = term_map.get(value[0], value[0])
    if len(value) >= 2:
        parsed["PSAM Present"] = {"0": "No", "1": "Yes"}.get(value[1], value[1])
    if len(value) >= 3:
        sec_map = {
            "0": "Specified by service code",
            "1": "No security concern",
            "2": "Suspected fraud",
            "3": "Stolen card",
        }
        parsed["Security Condition"] = sec_map.get(value[2], value[2])
    if len(value) >= 4:
        cat_map = {
            "0": "Not a CAT",
            "1": "CAT Level 1",
            "2": "CAT Level 2",
            "3": "CAT Level 3",
            "4": "CAT Level 4",
            "9": "Not Applicable",
        }
        parsed["CAT Level"] = cat_map.get(value[3], value[3])
    if len(value) >= 5:
        mode_map = {
            "0": "Unknown",
            "1": "Manual (key entry)",
            "2": "Magnetic stripe",
            "3": "Bar code",
            "4": "OCR",
            "5": "ICC (chip)",
            "6": "Key entry",
            "7": "NFC/Contactless",
            "8": "Fallback to magnetic stripe",
            "9": "Not Applicable",
            "A": "Contactless magnetic stripe",
            "B": "Contactless ICC",
        }
        parsed["Card Data Input Mode"] = mode_map.get(value[4], value[4])
    if len(value) >= 6:
        auth_map = {
            "0": "Not authenticated",
            "1": "PIN",
            "2": "Electronic signature",
            "3": "Biometrics",
            "4": "Biometrics + PIN",
            "5": "Electronic signature + PIN",
            "9": "Not Applicable",
            "S": "Signature (paper)",
        }
        parsed["Cardholder Auth Method"] = auth_map.get(value[5], value[5])
    if len(value) >= 7:
        entity_map = {
            "0": "Not authenticated",
            "1": "ICC - offline PIN",
            "2": "Card acceptance device",
            "3": "Authorizing agent - online PIN",
            "4": "Merchant - signature",
            "5": "Other",
            "9": "Not Applicable",
        }
        parsed["Cardholder Auth Entity"] = entity_map.get(value[6], value[6])
    if len(value) >= 8:
        out_map = {
            "0": "Unknown",
            "1": "None",
            "2": "Magnetic stripe write",
            "3": "ICC",
            "9": "Not Applicable",
        }
        parsed["Card Data Output Capability"] = out_map.get(value[7], value[7])
    if len(value) >= 9:
        term_map = {
            "0": "Unknown",
            "1": "None",
            "2": "Print, no electronic journal",
            "3": "Electronic journal, no print",
            "4": "Print and electronic journal",
            "9": "Not Applicable",
        }
        parsed["Terminal Output Capability"] = term_map.get(value[8], term_map.get(value[8], value[8]))
    if len(value) >= 10:
        pin_map = {
            "0": "Unknown",
            "1": "None",
            "2": "4 digits",
            "3": "5 digits",
            "4": "6 digits",
            "5": "7 digits",
            "6": "8 digits",
            "7": "9 digits",
            "8": "10 digits",
            "9": "11 digits",
            "A": "12 digits",
        }
        parsed["PIN Capture Capability"] = pin_map.get(value[9], value[9])
    if len(value) >= 11:
        env_map = {
            "0": "No terminal used",
            "1": "On card acceptor premises, attended",
            "2": "On card acceptor premises, unattended",
            "3": "Off card acceptor premises, attended",
            "4": "Off card acceptor premises, unattended",
            "5": "On cardholder premises",
            "9": "Not Applicable",
        }
        parsed["Operative Environment"] = env_map.get(value[10], value[10])
    return parsed


def _parse_se42(value: str) -> dict:
    """Parse SE42 E-Commerce Security Level Indicator and UCAF."""
    parsed = {}
    if len(value) >= 2:
        level_map = {
            "00": "Level 0 - No security",
            "10": "Level 1 - Merchant only",
            "11": "Level 2 - Cardholder authentication",
            "12": "Level 3 - Channel encrypted",
            "13": "Level 4 - Cardholder authenticated channel",
        }
        level = value[0:2]
        parsed["Security Level Indicator"] = level_map.get(level, level)
    if len(value) >= 3:
        coll_map = {
            "0": "Not supported",
            "1": "Supported, not populated",
            "2": "Supported, populated",
        }
        parsed["UCAF Collection Indicator"] = coll_map.get(value[2], value[2])
    return parsed


def _parse_se26(value: str) -> dict:
    """Parse SE26 Wallet Program Data."""
    parsed = {}
    if len(value) >= 4:
        wallet_map = {
            "MPGS": "Mastercard Payment Gateway Services",
            "GOOG": "Google Pay",
            "APPL": "Apple Pay",
            "SAMS": "Samsung Pay",
        }
        wid = value[0:4]
        parsed["Wallet Identifier"] = wallet_map.get(wid, wid)
    if len(value) >= 5:
        parsed["Wallet Program Data"] = value[4:]
    return parsed


def _parse_se23(value: str) -> dict:
    """Parse SE23 Payment Initiation Channel."""
    parsed = {}
    channel_map = {
        "00": "Not specified",
        "01": "Card present",
        "02": "Card not present - e-commerce",
        "03": "Card not present - mail order",
        "04": "Card not present - telephone order",
        "05": "Card not present - recurring",
        "06": "Card not present - installment",
        "07": "Card not present - digital wallet",
        "08": "Card not present - mobile commerce",
    }
    parsed["Payment Initiation Channel"] = channel_map.get(value, value)
    return parsed


# Subelement parsers dispatch table
SE_PARSERS = {
    "22": _parse_se22,
    "23": _parse_se23,
    "26": _parse_se26,
    "38": _parse_se38,
    "42": _parse_se42,
    "43": _parse_se43,
    "61": _parse_se61,
}


def parse_de48(de48_value: str) -> DE48ParseResult:
    """
    Parse Mastercard ISO 8583 DE48 (Field 48) value.

    Each subelement format: IILLLL...V
      II   = 2-digit subelement ID
      LLL  = 3-digit length (decimal)
      V... = value of given length

    Args:
        de48_value: The raw string value of DE48

    Returns:
        DE48ParseResult with all parsed subelements
    """
    subelements = []
    errors = []
    pos = 0
    raw = de48_value

    while pos < len(raw):
        remaining = len(raw) - pos

        # Need at least 5 chars: 2 (ID) + 3 (length)
        if remaining < 5:
            if remaining > 0:
                errors.append(
                    f"Trailing data at position {pos}: {raw[pos:]!r}"
                )
            break

        se_id = raw[pos:pos + 2]
        pos += 2

        length_str = raw[pos:pos + 3]
        pos += 3

        if not length_str.isdigit():
            errors.append(
                f"Invalid length '{length_str}' for SE{se_id} at position {pos - 3}"
            )
            break

        length = int(length_str)

        if pos + length > len(raw):
            errors.append(
                f"SE{se_id} length {length} exceeds remaining data at position {pos}"
            )
            value = raw[pos:]
            pos = len(raw)
        else:
            value = raw[pos:pos + length]
            pos += length

        se = Subelement(id=se_id, length=length, value=value)

        # Run sub-parser if available
        if se_id in SE_PARSERS:
            try:
                se.parsed_fields = SE_PARSERS[se_id](value)
            except Exception as exc:
                errors.append(f"SE{se_id} sub-parse error: {exc}")

        subelements.append(se)

    return DE48ParseResult(raw=raw, subelements=subelements, errors=errors)


def format_de48_report(result: DE48ParseResult, verbose: bool = True) -> str:
    """Format a human-readable DE48 parse report."""
    lines = [
        "=" * 60,
        "Mastercard ISO 8583 DE48 (Field 48) Parse Report",
        "=" * 60,
        f"Raw Value   : {result.raw!r}",
        f"Raw Length  : {len(result.raw)}",
        f"Subelements : {len(result.subelements)}",
        "",
    ]

    for se in result.subelements:
        label = f"SE{se.id}"
        if se.name:
            label += f" - {se.name}"
        lines.append(f"  {label}")
        lines.append(f"    Length : {se.length}")
        lines.append(f"    Value  : {se.value!r}")
        if verbose and se.parsed_fields:
            lines.append("    Fields :")
            for fname, fval in se.parsed_fields.items():
                lines.append(f"      {fname:<35}: {fval}")
        lines.append("")

    if result.errors:
        lines.append("Errors:")
        for err in result.errors:
            lines.append(f"  [!] {err}")

    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Example / demo usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example 1: E-commerce transaction with UCAF
    # SE22 (MPMI) + SE38 (E-Commerce Indicators) + SE43 (UCAF)
    example1 = (
        "22"  "014"  "10000000000000"
        "38"  "025"  "02ABCDEFGHIJKLMNOPQRST1XX"
        "43"  "029"  "2UCAF_DATA_SAMPLE_XXXXXXXXXXX"
        "61"  "011"  "10002500204"
    )

    # Example 2: Wallet (Google Pay) transaction
    example2 = (
        "23"  "002"  "07"
        "26"  "008"  "GOOG1234"
        "61"  "011"  "21002B10203"
        "22"  "004"  "0000"
    )

    # Example 3: Installment payment
    example3 = (
        "22"  "014"  "10000000011206"
        "61"  "011"  "10002500204"
        "63"  "015"  "123456789012345"
    )

    for i, example in enumerate([example1, example2, example3], 1):
        print(f"\n{'#' * 60}")
        print(f"# Example {i}")
        print('#' * 60)
        result = parse_de48(example)
        print(format_de48_report(result))
