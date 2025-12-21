import pytest
from shipping import ShippingService

pytestmark = pytest.mark.bottomup

def test_shipping_th_light():
    """Test TH region with weight <= 5"""
    ship = ShippingService()
    cost = ship.cost(5.0, "TH")
    assert cost == 50.0

def test_shipping_th_boundary_light():
    """Test TH region at exact boundary (5.0)"""
    ship = ShippingService()
    cost = ship.cost(5.0, "TH")
    assert cost == 50.0

def test_shipping_th_just_over_boundary():
    """Test TH region just over boundary (5.01)"""
    ship = ShippingService()
    cost = ship.cost(5.01, "TH")
    assert cost == 120.0

def test_shipping_th_heavy():
    """Test TH region with weight > 5"""
    ship = ShippingService()
    cost = ship.cost(10.0, "TH")
    assert cost == 120.0

def test_shipping_th_very_light():
    """Test TH region with very light weight"""
    ship = ShippingService()
    cost = ship.cost(0.5, "TH")
    assert cost == 50.0

def test_shipping_th_zero_weight():
    """Test TH region with zero weight"""
    ship = ShippingService()
    cost = ship.cost(0.0, "TH")
    assert cost == 50.0

def test_shipping_us_region():
    """Test US region (international)"""
    ship = ShippingService()
    cost = ship.cost(5.0, "US")
    assert cost == 300.0

def test_shipping_eu_region():
    """Test EU region (international)"""
    ship = ShippingService()
    cost = ship.cost(10.0, "EU")
    assert cost == 300.0

def test_shipping_unknown_region():
    """Test unknown region defaults to international rate"""
    ship = ShippingService()
    cost = ship.cost(3.0, "XX")
    assert cost == 300.0

def test_shipping_international_any_weight():
    """Test that international shipping cost is same regardless of weight"""
    ship = ShippingService()
    assert ship.cost(0.1, "US") == 300.0
    assert ship.cost(100.0, "US") == 300.0