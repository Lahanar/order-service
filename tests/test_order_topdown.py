import pytest
from inventory import InMemoryInventory
from shipping import ShippingService
from order import OrderService
from payment import PaymentDeclinedError
from emailer import EmailService

pytestmark = pytest.mark.topdown

class StubFailPayment:
    def charge(self, amount: float, currency: str) -> str:
        raise PaymentDeclinedError("simulated decline")
    def refund(self, transaction_id: str) -> None:
        return

class SpyEmail(EmailService):
    def __init__(self):
        self.sent = []
    def send(self, to, subject, body):
        self.sent.append((to, subject, body))

def test_payment_decline_releases_stock():
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    svc = OrderService(inv, StubFailPayment(), ShippingService(), SpyEmail())
    items = [{"sku":"SKU1","qty":3,"price":100.0,"weight":1.0}]
    with pytest.raises(PaymentDeclinedError):
        svc.place_order("a@b.com", items, region="TH")
    assert inv.get_stock("SKU1") == 10

def test_payment_decline_with_multiple_items_releases_all():
    """Test that payment decline releases all reserved items"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    inv.add_stock("SKU2", 20)
    svc = OrderService(inv, StubFailPayment(), ShippingService(), SpyEmail())
    items = [
        {"sku":"SKU1","qty":3,"price":100.0,"weight":1.0},
        {"sku":"SKU2","qty":5,"price":50.0,"weight":2.0}
    ]
    with pytest.raises(PaymentDeclinedError):
        svc.place_order("a@b.com", items, region="TH")
    assert inv.get_stock("SKU1") == 10
    assert inv.get_stock("SKU2") == 20

class StubPaymentAmountTooLow:
    """Stub that fails for amounts <= 0"""
    def charge(self, amount: float, currency: str) -> str:
        raise PaymentDeclinedError("invalid amount")
    def refund(self, transaction_id: str) -> None:
        return

def test_payment_invalid_amount_releases_stock():
    """Test payment failure due to invalid amount"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 5)
    svc = OrderService(inv, StubPaymentAmountTooLow(), ShippingService(), SpyEmail())
    items = [{"sku":"SKU1","qty":2,"price":100.0,"weight":1.0}]
    with pytest.raises(PaymentDeclinedError):
        svc.place_order("test@test.com", items, region="TH")
    assert inv.get_stock("SKU1") == 5

class StubPaymentSuccess:
    """Stub that always succeeds"""
    def charge(self, amount: float, currency: str) -> str:
        return "tx-stubbed-12345"
    def refund(self, transaction_id: str) -> None:
        return

def test_successful_order_sends_email():
    """Test that successful order sends confirmation email"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, StubPaymentSuccess(), ShippingService(), spy_email)
    items = [{"sku":"SKU1","qty":2,"price":100.0,"weight":1.0}]
    svc.place_order("customer@example.com", items, region="TH")
    
    assert len(spy_email.sent) == 1
    to, subject, body = spy_email.sent[0]
    assert to == "customer@example.com"
    assert subject == "Order confirmed"
    assert "tx-stubbed-12345" in body

def test_email_contains_total_amount():
    """Test that confirmation email contains total amount"""
    inv = InMemoryInventory()
    inv.add_stock("PROD1", 5)
    spy_email = SpyEmail()
    svc = OrderService(inv, StubPaymentSuccess(), ShippingService(), spy_email)
    items = [{"sku":"PROD1","qty":1,"price":200.0,"weight":3.0}]
    result = svc.place_order("user@test.com", items, region="TH")
    
    assert len(spy_email.sent) == 1
    _, _, body = spy_email.sent[0]
    assert f"{result['total']:.2f}" in body
    assert "250.00" in body  # 200 + 50 shipping

def test_email_failure_does_not_abort_order():
    """Test that email failure doesn't abort the order"""
    class FailingEmail(EmailService):
        def send(self, to, subject, body):
            raise Exception("Email service down")
    
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    svc = OrderService(inv, StubPaymentSuccess(), ShippingService(), FailingEmail())
    items = [{"sku":"SKU1","qty":2,"price":100.0,"weight":1.0}]
    
    # Should not raise exception despite email failure
    result = svc.place_order("test@test.com", items, region="TH")
    assert result["transaction_id"] == "tx-stubbed-12345"
    assert inv.get_stock("SKU1") == 8  # Stock still reserved

class StubShipping:
    """Stub shipping service for testing"""
    def __init__(self, fixed_cost: float):
        self.fixed_cost = fixed_cost
    def cost(self, total_weight: float, region: str) -> float:
        return self.fixed_cost

def test_order_total_calculation_with_stub_shipping():
    """Test that order total is calculated correctly"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM1", 10)
    svc = OrderService(inv, StubPaymentSuccess(), StubShipping(75.0), SpyEmail())
    items = [{"sku":"ITEM1","qty":2,"price":150.0,"weight":1.0}]
    result = svc.place_order("test@test.com", items, region="TH")
    
    assert result["total"] == 375.0  # (2*150) + 75
    assert result["shipping"] == 75.0
