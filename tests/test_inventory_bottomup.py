import pytest
from inventory import InMemoryInventory, InventoryError

pytestmark = pytest.mark.bottomup

def test_inventory_reserve_and_release():
    inv = InMemoryInventory()
    inv.add_stock("S", 5)
    inv.reserve("S", 3)
    assert inv.get_stock("S") == 2
    inv.release("S", 3)
    assert inv.get_stock("S") == 5

def test_inventory_not_enough_stock():
    inv = InMemoryInventory()
    inv.add_stock("S", 1)
    with pytest.raises(InventoryError):
        inv.reserve("S", 2)

def test_inventory_reserve_zero_quantity():
    """Test that reserving 0 quantity raises error"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.reserve("SKU1", 0)

def test_inventory_reserve_negative_quantity():
    """Test that reserving negative quantity raises error"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.reserve("SKU1", -5)

def test_inventory_release_zero_quantity():
    """Test that releasing 0 quantity raises error"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.release("SKU1", 0)

def test_inventory_release_negative_quantity():
    """Test that releasing negative quantity raises error"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.release("SKU1", -3)

def test_inventory_add_negative_stock():
    """Test that adding negative stock raises error"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="qty must be >= 0"):
        inv.add_stock("SKU1", -10)

def test_inventory_get_nonexistent_sku():
    """Test that getting stock for non-existent SKU returns 0"""
    inv = InMemoryInventory()
    assert inv.get_stock("NONEXISTENT") == 0

def test_inventory_reserve_from_nonexistent_sku():
    """Test that reserving from non-existent SKU raises error"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="not enough stock"):
        inv.reserve("NONEXISTENT", 1)

def test_inventory_multiple_skus():
    """Test inventory with multiple SKUs"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    inv.add_stock("SKU2", 20)
    inv.reserve("SKU1", 3)
    inv.reserve("SKU2", 5)
    assert inv.get_stock("SKU1") == 7
    assert inv.get_stock("SKU2") == 15
    