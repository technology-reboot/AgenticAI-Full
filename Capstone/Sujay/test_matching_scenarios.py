"""
Test Script: Matching Agent Scenarios
Tests the three-way match (PO, Invoice, Receipt) with various scenarios.

Each scenario tests different match conditions:
1. Perfect match: All amounts match within tolerance
2. Amount discrepancy: Invoice differs from PO/Receipt
3. Duplicate detection: Same invoice number
4. Policy threshold breach: Amount exceeds limit
5. Statistical outlier: Amount unusual for vendor
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.matching_agent import MatchingAgent
from agents.anomaly_agent import AnomalyAgent


def run_three_way_match(po_agent, invoice_data, receipt_data, label=""):
    """Run a three-way match test and display results."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {label}")
    print(f"{'='*60}")

    result = po_agent.three_way_match(
        po_data=po_data,
        invoice_data=invoice_data,
        receipt_data=receipt_data
    )

    # Display key results
    print(f"\nOverall Status: {result['overall_status']}")
    print(f"PO-Invoice Match: {result['po_invoice_match']}")
    print(f"Invoice-Receipt Match: {result['invoice_receipt_match']}")
    print(f"PO-Receipt Match: {result['po_receipt_match']}")
    print(f"Fuzzy Vendor Match: {result['fuzzy_vendor_match']}")

    if result['discrepancies']:
        print(f"\nDiscrepancies ({len(result['discrepancies'])}):")
        for d in result['discrepancies']:
            print(f"  - {d['type']}:")
            print(f"    Po: ${d['po_amount']:.2f}, Invoice: ${d['invoice_amount']:.2f}, "
                  f"Receipt: ${d['receipt_amount']:.2f}")
            print(f"    Difference: ${d['difference']:.2f} ({d['percent_difference']:.1f}%), "
                  f"Tolerance: {d['tolerance']:.1f}%")
    else:
        print("\nNo discrepancies - all amounts match within tolerance!")

    if result['matched_amounts']:
        print(f"Matched Amounts: {result['matched_amounts']}")

    return result


def test_scenario_perfect_match():
    """Test 1: All amounts match perfectly within tolerance."""
    agent = MatchingAgent(po_tolerance=2.0, invoice_tolerance=5.0, receipt_tolerance=5.0)

    po_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}
    invoice_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}
    receipt_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}

    run_three_way_match(agent, po_data, invoice_data, receipt_data, "PERFECT MATCH")


def test_scenario_invoice_discrepancy():
    """Test 2: Invoice amount differs from PO by more than tolerance."""
    agent = MatchingAgent(po_tolerance=2.0, invoice_tolerance=5.0, receipt_tolerance=5.0)

    po_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}
    invoice_data = {"total_amount": 1050.00, "vendor_name": "Acme Supplies"}  # 5% over
    receipt_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}

    run_three_way_match(agent, po_data, invoice_data, receipt_data, "INVOICE 5% OVER PO")


def test_scenario_receipt_discrepancy():
    """Test 3: Receipt amount differs from invoice."""
    agent = MatchingAgent(po_tolerance=2.0, invoice_tolerance=5.0, receipt_tolerance=5.0)

    po_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}
    invoice_data = {"total_amount": 1000.00, "vendor_name": "Acme Supplies"}
    receipt_data = {"total_amount": 970.00, "vendor_name": "Acme Supplies"}  # 3% under

    run_three_way_match(agent, po_data, invoice_data, receipt_data, "RECEIPT 3% UNDER INVOICE")


def test_scenario_duplicate_vendor():
    """Test 4: Same vendor, testing fuzzy matching."""
    agent = MatchingAgent(vendor_fuzzy_threshold=0.8)

    po_data = {"total_amount": 500.00, "vendor_name": "Acme Supplies"}
    invoice_data = {"total_amount": 500.00, "vendor_name": "Acme Supplies"}  # Slightly different formatting
    receipt_data = {"total_amount": 500.00, "vendor_name": "Acme Supply"}  # Missing 's'

    result = run_three_way_match(agent, po_data, invoice_data, receipt_data, "FUZZY VENDOR MATCH")
    print(f"  (Vendor similarity would be calculated by agent)")


def test_scenario_threshold_breach():
    """Test 5: Amount exceeds policy threshold (tested via anomaly agent)."""
    agent = AnomalyAgent(threshold_amount=1000.0)

    invoices = [
        {"invoice_number": "INV-TEST-001", "total_amount": 1500.00, "vendor_name": "Global Logistics"},
        {"invoice_number": "INV-TEST-002", "total_amount": 500.00, "vendor_name": "Acme Supplies"}
    ]

    print(f"\n{'='*60}")
    print(f"SCENARIO: POLICY THRESHOLD BREACH")
    print(f"{'='*60}")

    result = agent.detect_anomalies(invoices)

    print(f"\nTotal Anomalies: {result.summary['total_anomalies']}")
    print(f"By Type: {result.summary['by_type']}")
    print(f"Critical Count: {result.summary['critical_count']}")

    for anomaly in result.anomalies:
        print(f"  - {anomaly['type']}: {anomaly['description']}")
        print(f"    Amount: ${anomaly['amount']:.2f}, Severity: {anomaly['severity']}")


def test_scenario_outlier_detection():
    """Test 6: Statistical outlier against vendor history."""
    agent = AnomalyAgent(threshold_amount=1000.0, history_size=10)

    invoices = [
        {"invoice_number": "INV-TEST-001", "total_amount": 2500.00, "vendor_name": "TechCorp"},
        {"invoice_number": "INV-TEST-002", "total_amount": 895.50, "vendor_name": "TechCorp"}
    ]

    vendor_history = {
        "TechCorp": [
            {"invoice_number": "INV-2024-002", "total_amount": 895.50},
            {"invoice_number": "INV-2024-005", "total_amount": 950.00},
            {"invoice_number": "INV-2024-007", "total_amount": 920.00}
        ]
    }

    print(f"\n{'='*60}")
    print(f"SCENARIO: STATISTICAL OUTLIER DETECTION")
    print(f"{'='*60}")

    result = agent.detect_anomalies(invoices, vendor_history)

    print(f"\nTotal Anomalies: {result.summary['total_anomalies']}")
    print(f"By Type: {result.summary['by_type']}")

    for anomaly in result.anomalies:
        print(f"  - {anomaly['type']}: {anomaly['description']}")


def test_scenario_csv_data():
    """Test 7: Use actual CSV data from the project's data directory."""
    import csv
    from pathlib import Path

    print(f"\n{'='*60}")
    print(f"SCENARIO: REAL CSV DATA FROM PROJECT")
    print(f"{'='*60}")

    # Load CSV data
    def load_csv(path):
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

    po_data_list = load_csv(Path("data/purchase_orders.csv"))
    invoice_data_list = load_csv(Path("data/sample_invoices.csv"))
    receipt_data_list = load_csv(Path("data/sample_receipts.csv"))

    agent = MatchingAgent(po_tolerance=3.0, invoice_tolerance=5.0, receipt_tolerance=5.0)

    print(f"\nLoaded {len(po_data_list)} POs, {len(invoice_data_list)} invoices, {len(receipt_data_list)} receipts")

    # Test first 3 records
    for i in range(min(3, len(po_data_list))):
        po = po_data_list[i]
        invoice = invoice_data_list[i]
        receipt = receipt_data_list[i]

        po_data = {"total_amount": float(po['total_amount']), "vendor_name": po['vendor_name']}
        invoice_data = {"total_amount": float(invoice['total_amount']), "vendor_name": invoice['vendor_name']}
        receipt_data = {"total_amount": float(receipt['total_amount']), "vendor_name": receipt['vendor_name']}

        run_three_way_match(agent, po_data, invoice_data, receipt_data, f"Record {i+1}: {po['po_number']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MATCHING AGENT TEST SCENARIOS")
    print("Intelligent Invoice & Expense Reconciliation Agent")
    print("="*60 + "\n")

    test_scenario_perfect_match()
    test_scenario_invoice_discrepancy()
    test_scenario_receipt_discrepancy()
    test_scenario_duplicate_vendor()
    test_scenario_threshold_breach()
    test_scenario_outlier_detection()
    test_scenario_csv_data()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60 + "\n")