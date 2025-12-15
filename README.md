# A2.2: Integration Testing Automation — Order Service

เป้าหมาย
- ฝึกทำ Integration Testing 3 แบบ: Top-down, Bottom-up, Sandwich
- ฝึกเขียน Stub/Driver/Spy
- เข้าใจการแยกส่วนบริการ (Inventory, Payment, Shipping, Email) และการรวมระบบ

---

วิธีเริ่มต้น
1) ติดตั้ง dependencies
   pip install -r requirements.txt
2) รันทดสอบ
   pytest -q

แบบฝึกหัดที่ต้องทำ
- ทำความเข้าใจโค้ดในไฟล์: inventory.py, payment.py, shipping.py, emailer.py, order.py
- ทำเทสต์ครบ 3 แบบ: Top-down, Bottom-up, Sandwich 
     - อ่านเทสต์ตัวอย่างใน tests/ แล้ว:
            1) เพิ่มกรณีทดสอบ Top-down:
               - เขียน StubPayment ที่ล้มเหลวแบบต่างๆ
               - เพิ่ม SpyEmail ตรวจ subject/body
            2) เพิ่มกรณีทดสอบ Bottom-up:
               - เพิ่มเทสต์ reserve/release ที่ขอบเขต
            3) เพิ่มกรณีทดสอบ Sandwich:
               - ใช้ SimplePayment จริง + Email spy
               - เพิ่ม region อื่น (เช่น "US")
- Automation/CI: ตั้งค่าให้เทสต์เหล่านี้รันอัตโนมัติบน GitHub Actions ทุกครั้งที่ push/PR และได้ผลลัพธ์ที่เชื่อถือได้
     - รันเฉพาะหมวดได้ เช่น pytest -m topdown -q
     - ปรับ GitHub Actions ให้ทำ coverage,
- สรุปสิ่งที่ค้นพบสั้นๆ (อย่างต่ำ 10 บรรทัด) 

## What You Must Do (Checklist)

### Read
- `inventory.py`
- `payment.py`
- `shipping.py`
- `emailer.py`
- `order.py`

### High-Level Call Graph
OrderService  
├── InventoryRepository  
│       ├── reserve()  
│       └── release()  
│  
├── ShippingService  
│   └── cost()  
│  
├── PaymentGateway  
│   └── charge()  
│  
└── EmailService  
    └── send()


### Extend Tests (see TODOs)
1. **Top-down**
   - Add failing payment cases
   - Verify email subject/body using Spy

2. **Bottom-up**
   - Add boundary tests for inventory errors

3. **Sandwich**
   - Test shipping cost for `"US"`
   - Test weight > 5kg in `"TH"`

### Reflect
- Write **5–10 lines** summarizing:
  - What broke?
  - What integration risks you found?

---

## System Overview

OrderService  
├─ Inventory  
├─ Payment  
├─ Shipping  
└─ Email  
