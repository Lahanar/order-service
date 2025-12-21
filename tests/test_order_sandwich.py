import pytest
from inventory import InMemoryInventory
from payment import SimplePayment,PaymentDeclinedError
from shipping import ShippingService
from order import OrderService
from emailer import EmailService

pytestmark = pytest.mark.sandwich

class SpyEmail(EmailService):
    def __init__(self): 
        self.calls = 0
        self.sent = []
    def send(self, to, subject, body): 
        self.calls += 1
        self.sent.append((to, subject, body))

def test_order_success_with_real_payment():
    inv = InMemoryInventory()
    inv.add_stock("A", 2)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"A","qty":1,"price":900.0,"weight":2.0}]
    res = svc.place_order("x@y.com", items, region="TH")
    assert inv.get_stock("A") == 1

def test_order_success_us_region():
    """Test successful order with US region (international shipping)"""
    inv = InMemoryInventory()
    inv.add_stock("PROD1", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"PROD1","qty":1,"price":500.0,"weight":3.0}]
    result = svc.place_order("user@example.com", items, region="US")
    
    assert result["total"] == 800.0  # 500 + 300 (international)
    assert result["shipping"] == 300.0
    assert inv.get_stock("PROD1") == 9
    assert spy_email.calls == 1

def test_order_success_eu_region():
    """Test successful order with EU region"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM1", 5)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"ITEM1","qty":2,"price":200.0,"weight":2.0}]
    result = svc.place_order("customer@test.com", items, region="EU")
    
    assert result["total"] == 700.0  # 400 + 300
    assert result["shipping"] == 300.0
    assert spy_email.calls == 1

def test_order_th_weight_boundary_light():
    """Test TH region with weight exactly at 5.0 (light shipping)"""
    inv = InMemoryInventory()
    inv.add_stock("LIGHT", 10)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"LIGHT","qty":1,"price":100.0,"weight":5.0}]
    result = svc.place_order("test@test.com", items, region="TH")
    
    assert result["shipping"] == 50.0
    assert result["total"] == 150.0

def test_order_th_weight_boundary_heavy():
    """Test TH region with weight just over 5.0 (heavy shipping)"""
    inv = InMemoryInventory()
    inv.add_stock("HEAVY", 10)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"HEAVY","qty":1,"price":100.0,"weight":5.01}]
    result = svc.place_order("test@test.com", items, region="TH")
    
    assert result["shipping"] == 120.0
    assert result["total"] == 220.0

def test_order_multiple_items_total_calculation():
    """Test order with multiple items calculates total correctly"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM1", 10)
    inv.add_stock("ITEM2", 10)
    inv.add_stock("ITEM3", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    
    items = [
        {"sku":"ITEM1","qty":2,"price":100.0,"weight":1.0},
        {"sku":"ITEM2","qty":1,"price":150.0,"weight":2.0},
        {"sku":"ITEM3","qty":3,"price":50.0,"weight":0.5}
    ]
    result = svc.place_order("multi@test.com", items, region="TH")
    
    # Subtotal: (2*100) + (1*150) + (3*50) = 500
    # Weight: (2*1) + (1*2) + (3*0.5) = 5.5 > 5, so shipping = 120
    # Total: 500 + 120 = 620
    assert result["total"] == 620.0
    assert result["shipping"] == 120.0
    assert inv.get_stock("ITEM1") == 8
    assert inv.get_stock("ITEM2") == 9
    assert inv.get_stock("ITEM3") == 7

def test_order_payment_decline_above_1000():
    """Test that payment above 1000 is declined and stock is released"""
    inv = InMemoryInventory()
    inv.add_stock("EXPENSIVE", 5)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"EXPENSIVE","qty":1,"price":950.0,"weight":6.0}]
    
    # Total: 950 + 120 = 1070 > 1000, should decline
    with pytest.raises(PaymentDeclinedError):
        svc.place_order("test@test.com", items, region="TH")
    
    # Stock should be released
    assert inv.get_stock("EXPENSIVE") == 5

def test_order_payment_at_1000_boundary():
    """Test payment at exactly 1000 boundary (should succeed)"""
    inv = InMemoryInventory()
    inv.add_stock("PROD", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"PROD","qty":1,"price":950.0,"weight":2.0}]
    
    # Total: 950 + 50 = 1000 (exactly at limit)
    result = svc.place_order("test@test.com", items, region="TH")
    assert result["total"] == 1000.0
    assert spy_email.calls == 1

def test_order_insufficient_stock():
    """Test that insufficient stock raises InventoryError"""
    from inventory import InventoryError
    inv = InMemoryInventory()
    inv.add_stock("LIMITED", 2)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"LIMITED","qty":5,"price":100.0,"weight":1.0}]
    
    with pytest.raises(InventoryError):
        svc.place_order("test@test.com", items, region="TH")
    
    # Stock should remain unchanged
    assert inv.get_stock("LIMITED") == 2

def test_order_email_verification():
    """Test that email contains correct information"""
    inv = InMemoryInventory()
    inv.add_stock("PROD", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"PROD","qty":1,"price":300.0,"weight":3.0}]
    result = svc.place_order("verify@test.com", items, region="TH")
    
    assert len(spy_email.sent) == 1
    to, subject, body = spy_email.sent[0]
    assert to == "verify@test.com"
    assert subject == "Order confirmed"
    assert "350.00 THB" in body
    assert result["transaction_id"] in body

def test_order_rounding():
    """Test that total is properly rounded to 2 decimal places"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM", 10)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"ITEM","qty":3,"price":33.333,"weight":1.0}]
    result = svc.place_order("test@test.com", items, region="TH")
    
    # Subtotal: 3 * 33.333 = 99.999
    # Total: 99.999 + 50 = 149.999
    # Should round to 150.00
    assert result["total"] == 150.0
    assert isinstance(result["total"], float)
