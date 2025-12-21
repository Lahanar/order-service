import pytest
from payment import SimplePayment, PaymentDeclinedError

pytestmark = pytest.mark.bottomup

def test_payment_valid_amount():
    """Test successful payment with valid amount"""
    pay = SimplePayment()
    tx_id = pay.charge(100.0, "THB")
    assert tx_id == "tx-10000"

def test_payment_boundary_valid_max():
    """Test payment at maximum valid amount (1000)"""
    pay = SimplePayment()
    tx_id = pay.charge(1000.0, "THB")
    assert tx_id == "tx-100000"

def test_payment_boundary_valid_min():
    """Test payment at minimum valid amount (just above 0)"""
    pay = SimplePayment()
    tx_id = pay.charge(0.01, "THB")
    assert tx_id == "tx-1"

def test_payment_amount_zero():
    """Test that payment with 0 amount is declined"""
    pay = SimplePayment()
    with pytest.raises(PaymentDeclinedError, match="invalid amount"):
        pay.charge(0.0, "THB")

def test_payment_amount_negative():
    """Test that payment with negative amount is declined"""
    pay = SimplePayment()
    with pytest.raises(PaymentDeclinedError, match="invalid amount"):
        pay.charge(-50.0, "THB")

def test_payment_amount_too_high():
    """Test that payment above 1000 is declined"""
    pay = SimplePayment()
    with pytest.raises(PaymentDeclinedError, match="amount too high"):
        pay.charge(1000.01, "THB")

def test_payment_amount_very_high():
    """Test that payment far above limit is declined"""
    pay = SimplePayment()
    with pytest.raises(PaymentDeclinedError, match="amount too high"):
        pay.charge(5000.0, "THB")

def test_payment_refund():
    """Test refund operation (no-op in current implementation)"""
    pay = SimplePayment()
    # Should not raise any exception
    pay.refund("tx-12345")

def test_payment_transaction_id_format():
    """Test that transaction ID follows expected format"""
    pay = SimplePayment()
    tx_id = pay.charge(123.45, "THB")
    assert tx_id.startswith("tx-")
    assert tx_id == "tx-12345"