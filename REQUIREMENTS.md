# Requirements of Order Service

## ภาพรวมระบบ

* ระบบสั่งซื้อ (OrderService) เชื่อมต่อ 4 องค์ประกอบ:

  * **Inventory**: จัดการสต็อก
  * **Payment**: ชำระเงิน
  * **Shipping**: ค่าขนส่ง
  * **Email**: ส่งอีเมลยืนยัน
* โจทย์เน้นฝึก **Integration Testing** 3 แบบ: **Top-down, Bottom-up, Sandwich** พร้อมการเขียน **Stub / Driver / Spy**

## ขอบเขต

### In-scope

* วงจรสั่งซื้อ: reserve stock → คำนวณราคา/ค่าส่ง → ชำระเงิน → ส่งอีเมล
* กติกาอนุมัติ/ปฏิเสธการจ่ายเงินแบบง่าย
* พฤติกรรมเมื่อจ่ายไม่ผ่านต้องคืนสต็อก

### Out-of-scope

* Persistence จริง (ใช้ InMemory)
* ระบบผู้ใช้/ที่อยู่/ภาษี/ส่วนลด
* Concurrency และ idempotency (อยู่ในแบบยาก)

## คำนิยามข้อมูล

* **LineItem**: `{ sku: str, qty: int>0, price: float>0, weight: float>0 }`
* **Region**: `"TH"` หรืออื่นๆ (เช่น `"US"`, `"EU"`)
* **สกุลเงิน**: `"THB"` ตลอด

## ข้อกำหนดเชิงหน้าที่ (Functional Requirements)

### FR1 Inventory

* `add_stock(sku, qty)`: เพิ่มสต็อก; `qty` ต้อง >= 0 มิฉะนั้นโยน `InventoryError`
* `get_stock(sku)`: คืนจำนวนคงเหลือ (`int`)
* `reserve(sku, qty)`: หักสต็อก; `qty` ต้อง > 0 และต้องมีสต็อกพอ มิฉะนั้นโยน `InventoryError`
* `release(sku, qty)`: คืนสต็อก; `qty` ต้อง > 0 มิฉะนั้นโยน `InventoryError`

### FR2 Shipping

* `cost(total_weight, region)`:

  * ถ้า `region = "TH"`: `total_weight <= 5` → `50.0`; `> 5` → `120.0`
  * อื่นๆ → `300.0`

### FR3 Payment (SimplePayment)

* `charge(amount, currency) → transaction_id (str)`

  * `amount <= 0` → ปฏิเสธ (`PaymentDeclinedError`)
  * `amount > 1000` → ปฏิเสธ (`PaymentDeclinedError`)
  * กรณีอื่น → อนุมัติ คืนค่า `"tx-<some-id>"`
* `refund(transaction_id)`: no-op (ไม่ใช้ในแบบฝึกหัด)

### FR4 OrderService.place_order(customer_email, items, region) → dict

* แปลง `items` เป็น `LineItem`
* ขั้นตอน:

  1. Reserve stock สำหรับทุกรายการ; ถ้าไม่พอ → โยน `InventoryError` และยุติ
  2. คำนวณ `subtotal = Σ(qty*price)`, `total_weight = Σ(qty*weight)`
  3. คำนวณ shipping ด้วย `ShippingService.cost(total_weight, region)`
  4. `total = subtotal + shipping`; ปัดทศนิยม 2 ตำแหน่งตอนคืนค่า
  5. เรียก `Payment.charge(total, "THB")`:

     * ถ้าปฏิเสธ → `release` stock ทั้งหมด แล้วโยน `PaymentDeclinedError`
  6. เรียก `EmailService.send(email, "Order confirmed", body)` เพื่อยืนยัน:

     * หากส่งอีเมลล้มเหลว ให้เพิกเฉย ไม่ย้อนกลับคำสั่งซื้อ
* ผลลัพธ์ต้องมี:

  * `total` (float, 2 ตำแหน่ง), `shipping` (float, 2 ตำแหน่ง), `transaction_id` (str)

## ข้อกำหนดเชิงไม่ใช่หน้าที่ (Non-Functional Requirements)

* ภาษา/สภาพแวดล้อม: Python 3.10+; ใช้ `pytest`
* ความสามารถทดสอบ: เทสต์ต้องรันผ่านใน GitHub Actions (workflow ที่ให้ไว้)
* เวลา: เทสต์ทั้งหมดควรรันได้ภายในไม่กี่วินาทีบนเครื่องมาตรฐาน/CI

## ข้อสมมติ

* items มี type ถูกต้อง
* ไม่มีค่าใช้จ่ายอื่นนอกจาก shipping
* ไม่พิจารณา security / auth

---

## Acceptance Criteria Table

| ID | Requirement | Acceptance Criteria | Covered By Tests |
|----|------------|--------------------|-----------------|
| AC-INV-01 | add_stock | qty < 0 → InventoryError |        |
| AC-INV-02 | reserve | qty > stock → InventoryError |        |
| AC-INV-03 | reserve | qty ≤ 0 → InventoryError |         |
| AC-INV-04 | release | qty ≤ 0 → InventoryError |         |
| AC-INV-05 | reserve+release | stock ถูกหักและคืนถูกต้อง |          |
| AC-SHIP-01 | shipping TH ≤5kg | cost = 50 |         |
| AC-SHIP-02 | shipping TH >5kg | cost = 120 |         |
| AC-SHIP-03 | shipping non-TH | cost = 300 |          |
| AC-PAY-01 | payment amount ≤0 | declined |         |
| AC-PAY-02 | payment amount >1000 | declined |          |
| AC-PAY-03 | payment valid | tx_id returned |          |
| AC-ORD-01 | payment fail | stock released |          |
| AC-ORD-02 | success order | email sent |         |
| AC-ORD-03 | email failure | order still succeeds |         |
| AC-ORD-04 | total calculation | subtotal + shipping |         |

---

## Mapping to Current Test Files

### tests/test_inventory_bottomup.py
Covers:
- 

Missing:
- 
---

### tests/test_order_topdown.py
Covers:
- 

Missing:
- 
---

### tests/test_order_sandwich.py
Covers:
- 

Missing:
- 

---

## Non-Functional Requirements

- Python 3.10+
- pytest
- CI ผ่าน GitHub Actions
- เทสต์ทั้งหมดควรรันภายในไม่กี่วินาที

---


