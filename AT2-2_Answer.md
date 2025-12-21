# AT2-2 Assignment Answers

**Student ID**: 650610753

---

## 1. สิ่งที่ค้นพบว่าระบบไม่เป็นไปตามที่คาดหวังไว้ หรือปัญหาที่ไม่คิดว่าจะเจอ (อย่างต่ำ 5 บรรทัด)

### Finding 1: Stock Release Logic on Payment Failure

เมื่อเริ่มทดสอบพบว่า OrderService มีกลไกการคืนสต็อกที่ดีเมื่อการชำระเงินล้มเหลว แต่ต้องตรวจสอบให้แน่ใจว่าทำงานถูกต้องกับหลายรายการ จากการทดสอบด้วย `test_payment_decline_with_multiple_items_releases_all()` พบว่าระบบสามารถคืนสต็อกให้ทุก SKU ได้อย่างถูกต้อง แต่ในการพัฒนาจริงอาจมีปัญหาถ้า reserve ทำครึ่งหนึ่งสำเร็จแล้วครึ่งหนึ่งล้มเหลว - ระบบปัจจุบันจะ raise error ทันทีโดยไม่คืนสต็อกที่ reserve ไปแล้ว ซึ่งอาจทำให้เกิด stock leak ได้

### Finding 2: Email Failure Handling

พบว่าระบบจัดการกับความล้มเหลวของ email service อย่างถูกต้องโดยใช้ try-except และทำให้คำสั่งซื้อสำเร็จต่อไป แต่ในระบบจริง การที่ลูกค้าไม่ได้รับอีเมลยืนยันอาจทำให้เกิดปัญหา ควรมี logging หรือ retry mechanism หรืออย่างน้อยควรบันทึกว่าการส่งอีเมลล้มเหลว เพื่อให้ admin สามารถติดตามได้

### Finding 3: Payment Amount Boundary at 1000

เมื่อทดสอบ boundary conditions พบว่า amount ที่ 1000 พอดีจะ approve แต่ 1000.01 จะ decline ซึ่งถูกต้องตาม spec แต่ในการใช้งานจริงอาจทำให้ลูกค้าสับสนเมื่อต้นทุนสินค้า + ค่าส่ง รวมแล้วเกิน 1000 เล็กน้อย ควรมี error message ที่ชัดเจนกว่า "amount too high" เช่น "Order total exceeds maximum limit of 1000 THB"

### Finding 4: Zero Weight Shipping Cost

พบว่าเมื่อ weight = 0 ระบบจะคิดค่าส่งในอัตรา light weight (50 THB for TH) ซึ่งอาจไม่สมเหตุสมผลในบางกรณี ตัวอย่างเช่น สินค้าดิจิทัลที่ไม่มี weight ก็ยังต้องจ่ายค่าส่ง ในระบบจริงอาจต้องมี business rule พิเศษสำหรับสินค้าที่ weight = 0

### Finding 5: Transaction ID Format Dependency

พบว่า transaction ID ถูกสร้างจาก amount \* 100 ซึ่งอาจทำให้เกิด collision ถ้ามี order หลายรายการที่มี amount เท่ากัน ในระบบจริงควรใช้ UUID หรือ sequential ID ที่รับประกันความ unique และควรมี timestamp เพื่อการ audit trail

### Finding 6: Inventory Reserve Before Payment Check

ระบบจะ reserve stock ก่อนตรวจสอบว่า payment จะผ่านหรือไม่ ซึ่งในกรณีที่ payment ล้มเหลวบ่อยๆ อาจทำให้ stock ถูก lock แล้ว release บ่อยเกินไป อาจควรมีการ validate payment amount ก่อน reserve stock หรืออย่างน้อยควรมี timeout สำหรับ reserved stock

---

## 2. การทดสอบโค้ดนี้แบบอัตโนมัติ มีข้อดี ข้อเสียอะไรบ้าง

### ข้อดี (Advantages)

1. **รวดเร็วและสม่ำเสมอ (Fast & Consistent)**

   - รัน test 47 cases ได้ภายใน 0.12 วินาที
   - ผลลัพธ์เหมือนเดิมทุกครั้งที่รัน (deterministic)
   - สามารถรันได้บ่อยๆ โดยไม่มีต้นทุนเพิ่ม

2. **ตรวจจับ Regression ได้ทันที (Regression Detection)**

   - เมื่อแก้โค้ดส่วนหนึ่ง สามารถรัน test ทั้งหมดเพื่อดูว่ามีผลกระทบกับส่วนอื่นไหม
   - ป้องกันการ break existing functionality เมื่อเพิ่ม feature ใหม่

3. **Documentation ที่รันได้ (Executable Documentation)**

   - Test cases แสดงให้เห็นว่าระบบควรทำงานอย่างไร
   - Developer คนใหม่สามารถเข้าใจ business logic จาก test cases

4. **เพิ่มความมั่นใจในการ Refactor (Refactoring Confidence)**

   - สามารถปรับปรุงโครงสร้างโค้ดได้โดยมั่นใจว่าพฤติกรรมยังคงเหมือนเดิม
   - Coverage 99% ทำให้มั่นใจว่าครอบคลุมเกือบทุก code path

5. **Integration กับ CI/CD (CI/CD Integration)**

   - รัน test อัตโนมัติทุกครั้งที่ commit code
   - ป้องกันไม่ให้ code ที่มีปัญหา merge เข้า main branch

6. **ประหยัดเวลาในระยะยาว (Long-term Time Savings)**
   - แม้ว่าเขียน test จะใช้เวลา แต่ประหยัดเวลาในการ debug และ manual testing มากกว่า

### ข้อเสีย (Disadvantages)

1. **เวลาและความพยายามในการเขียน (Initial Time Investment)**

   - ใช้เวลาเขียน test 47 cases นานกว่าเขียนแค่ production code
   - ต้องเรียนรู้ testing framework และ best practices

2. **ต้องดูแลรักษา Test Code (Maintenance Overhead)**

   - เมื่อ business logic เปลี่ยน ต้องแก้ทั้ง production code และ test code
   - Test code ก็เป็น code ที่อาจมี bug ได้เช่นกัน

3. **False Sense of Security (ความมั่นใจที่ผิดพลาด)**

   - Coverage 99% ไม่ได้หมายความว่าไม่มี bug
   - อาจมี edge cases หรือ integration scenarios ที่ไม่ได้ test

4. **ไม่ครอบคลุม Non-functional Requirements**

   - Test ปัจจุบันไม่ได้ทดสอบ performance, security, usability
   - ไม่ได้ test concurrency issues หรือ race conditions

5. **Flaky Tests ในบางกรณี**

   - ถ้า test พึ่งพา timing หรือ external dependencies จริงๆ อาจทำให้ test fail บางครั้ง
   - ต้องใช้ test doubles (stubs/mocks) อย่างระมัดระวัง

6. **ไม่ทดแทนการทดสอบอื่นๆ ได้ทั้งหมด**
   - ยังต้องมี manual testing, UAT, exploratory testing
   - ไม่สามารถทดสอบ user experience หรือ business value

---

## 3. ขั้นตอนการทำให้เทสต์รันอัตโนมัติอย่างเป็นระบบที่ทำในกิจกรรมนี้ คืออะไร

### ขั้นตอนที่ 1: Setup Testing Framework

1. สร้าง `requirements.txt` ที่มี `pytest>=7.0` และ `pytest-cov>=4.0`
2. ติดตั้ง dependencies: `pip install -r requirements.txt`
3. สร้าง folder `tests/` สำหรับเก็บ test files
4. สร้าง `tests/conftest.py` เพื่อ configure Python path

### ขั้นตอนที่ 2: Organize Tests by Strategy

1. สร้าง test files แยกตามแนวทาง integration testing:
   - `test_inventory_bottomup.py` - Bottom-up tests สำหรับ Inventory
   - `test_payment_bottomup.py` - Bottom-up tests สำหรับ Payment
   - `test_shipping_bottomup.py` - Bottom-up tests สำหรับ Shipping
   - `test_order_topdown.py` - Top-down tests ด้วย stubs
   - `test_order_sandwich.py` - Sandwich tests ด้วย real components

### ขั้นตอนที่ 3: Configure Pytest Markers

1. สร้าง `pytest.ini` เพื่อ define custom markers:
   ```ini
   [pytest]
   markers =
       topdown: Top-down integration tests
       bottomup: Bottom-up integration tests
       sandwich: Sandwich integration tests
   ```
2. ใส่ marker ในแต่ละ test file: `pytestmark = pytest.mark.bottomup`

### ขั้นตอนที่ 4: Write Test Cases

1. เขียน test cases ครบทั้ง 3 แนวทาง:
   - Bottom-up: ทดสอบ component แต่ละตัวแยก (29 tests)
   - Top-down: ทดสอบจาก OrderService ลงมาด้วย stubs (7 tests)
   - Sandwich: ทดสอบ integration จริงด้วย real components (11 tests)
2. ใช้ naming convention: `test_<component>_<scenario>`
3. เขียน docstrings อธิบายแต่ละ test

### ขั้นตอนที่ 5: Create Test Doubles

1. สร้าง Stubs สำหรับ top-down testing:
   - `StubFailPayment` - จำลองการชำระเงินล้มเหลว
   - `StubPaymentSuccess` - จำลองการชำระเงินสำเร็จ
   - `StubShipping` - ควบคุมค่าขนส่ง
2. สร้าง Spies สำหรับตรวจสอบ side effects:
   - `SpyEmail` - ตรวจว่ามีการส่ง email หรือไม่และเนื้อหาอะไร

### ขั้นตอนที่ 6: Run Tests Locally

1. รัน test ทั้งหมด: `pytest -v`
2. รัน test แยกตาม marker:
   - `pytest -m bottomup -v`
   - `pytest -m topdown -v`
   - `pytest -m sandwich -v`
3. ตรวจสอบว่าทุก test ผ่าน

### ขั้นตอนที่ 7: Measure Coverage

1. รัน pytest พร้อม coverage: `pytest --cov=. --cov-report=html`
2. ดู coverage report ใน terminal และ HTML report
3. ระบุส่วนที่ coverage ยังไม่ครบและเพิ่ม test cases
4. Target: ได้ coverage ≥ 90%

### ขั้นตอนที่ 8: Setup CI/CD (GitHub Actions)

1. สร้าง `.github/workflows/python-tests.yml`:
   ```yaml
   name: tests
   on: [push, pull_request]
   jobs:
     pytest:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
         - run: pip install -r requirements.txt
         - run: pytest -q
   ```
2. Commit และ push code ขึ้น GitHub
3. ตรวจสอบว่า GitHub Actions รัน test สำเร็จ

### ขั้นตอนที่ 9: Documentation

1. สร้าง `TEST_SUMMARY.md` สรุปผลการทดสอบ
2. สร้าง `PROJECT_OVERVIEW.md` อธิบายโครงสร้างโปรเจค
3. Update `README.md` ให้มีคำแนะนำการรัน test

### ขั้นตอนที่ 10: Continuous Improvement

1. Monitor test results ใน CI
2. เพิ่ม test cases เมื่อพบ bugs ใหม่
3. Refactor tests เมื่อมี code duplication
4. Review และ update tests เมื่อ requirements เปลี่ยน

---

## 4. ชุดทดสอบตั้งต้น ได้ coverage เท่าไร เมื่อเพิ่มกรณีทดสอบแล้ว ได้ coverage เท่าไร

### ชุดทดสอบตั้งต้น (Initial Test Suite)

**จำนวน Tests**: 4 tests

- `test_inventory_reserve_and_release` (Bottom-up)
- `test_inventory_not_enough_stock` (Bottom-up)
- `test_payment_decline_releases_stock` (Top-down)
- `test_order_success_with_real_payment` (Sandwich)

**Coverage จริงที่วัดได้**: **91%** (126/139 statements covered, 13 missing)

**รายละเอียด Coverage ตั้งต้น**:
| Component | Statements | Coverage |
|-----------|-----------|----------|
| emailer.py | 2 | 100% ✅ |
| inventory.py | 24 | 88% ⚠️ (3 missing) |
| order.py | 40 | 90% ⚠️ (4 missing) |
| payment.py | 13 | 77% ⚠️ (3 missing) |
| shipping.py | 5 | 80% ⚠️ (1 missing) |
| tests/conftest.py | 2 | 100% ✅ |
| **TOTAL** | **139** | **91%** |

### ชุดทดสอบหลังเพิ่ม (Enhanced Test Suite)

**จำนวน Tests**: 47 tests (+43 tests)

**Breakdown**:

- Bottom-up: 29 tests (Inventory: 10, Payment: 9, Shipping: 10)
- Top-down: 7 tests
- Sandwich: 11 tests

**Coverage**: **99%** (439/442 statements covered)

**Production Code Coverage**:

- emailer.py: 100% (2/2 statements)
- inventory.py: 100% (24/24 statements)
- order.py: 100% (40/40 statements)
- payment.py: 100% (13/13 statements)
- shipping.py: 100% (5/5 statements)

**Missing Coverage** (3 statements):

- 3 lines ใน test helper classes (StubPaymentAmountTooLow.refund, FailingEmail, StubShipping.**init**)
- ไม่จำเป็นต้อง test เพราะเป็น test helpers ไม่ใช่ production code

### สรุปการปรับปรุง Coverage

**ชุดทดสอบตั้งต้น (4 tests)**:

- Total Statements: 139
- Covered: 126 statements
- Missing: 13 statements
- **Coverage: 91%**

**ชุดทดสอบหลังเพิ่ม (47 tests)**:

- Total Statements: 442 (เพิ่มขึ้นเพราะมี test code มากขึ้น)
- Covered: 439 statements
- Missing: 3 statements (test helpers only)
- **Coverage: 99%**

**Production Code Coverage**:

- ตั้งต้น: inventory 88%, payment 77%, shipping 80%, order 90%
- หลังเพิ่ม: **ทุก component 100%** ✅

**การปรับปรุง**:

- Coverage เพิ่มขึ้น: **91% → 99%** (+8% overall)
- Production code: **~85% → 100%** (+15%)
- จำนวน test cases: **4 → 47** (+1,075%)
- Missing statements: **13 → 3** (-77%)

**ข้อสังเกต**:

- การเพิ่ม test 43 cases ทำให้ production code ครบ 100% ทุก modules
- 3 statements ที่เหลือเป็น test helper classes ที่ไม่จำเป็นต้อง test
- Bottom-up testing ช่วยให้ได้ coverage ของ individual components ครบถ้วน
- Top-down และ Sandwich testing ช่วยให้ได้ integration paths ที่ซับซ้อนขึ้น

---

## 5. เป็นไปได้ไหมที่จะทำให้ได้ 100% integration test coverage ให้เหตุผล (อย่างต่ำ 3-4 บรรทัด)

### คำตอบ: เป็นไปได้ยาก และไม่จำเป็นต้องเป็น 100%

**เหตุผลทางเทคนิค**:

1. **Code Coverage ≠ Integration Coverage**

   - แม้จะได้ 100% line coverage ก็ไม่ได้หมายความว่าทดสอบทุก integration path
   - ตัวอย่าง: ถ้ามี 3 components แต่ละตัวมี 2 states = 2³ = 8 combinations
   - จำนวน integration scenarios เติบโตแบบ exponential ตามจำนวน components

2. **Combinatorial Explosion**

   - ระบบของเรามี 4 dependencies (Inventory, Payment, Shipping, Email)
   - แต่ละ dependency มีหลาย states (success, various failures, boundary conditions)
   - การทดสอบทุก combination เป็นไปไม่ได้ในทางปฏิบัติ

3. **External Dependencies และ Non-deterministic Behavior**

   - บาง integration scenarios เกี่ยวข้องกับ timing, network, concurrency
   - Race conditions หรือ intermittent failures ยากต่อการ reproduce consistently
   - ตัวอย่าง: ถ้ามี real database หรือ external API calls

4. **Diminishing Returns**
   - การเพิ่ม coverage จาก 99% เป็น 100% อาจต้องใช้ความพยายามมาก
   - แต่ได้ value น้อยมาก (ส่วนที่เหลือมักเป็น edge cases ที่หายากมาก)
   - เวลาควรใช้เขียน test cases ที่มี business value มากกว่า

**ข้อยกเว้นที่ทำให้ 100% เป็นไปไม่ได้**:

1. **Test Helper Code**: Code ที่เขียนเพื่อ support tests เอง (stubs, spies) ไม่จำเป็นต้อง test
2. **Error Handling ที่หายากมาก**: เช่น OutOfMemory, system crash ทดสอบยาก
3. **Third-party Integration**: ถ้าต้อง integrate กับ real external services ทดสอบทุก scenario ไม่ได้

**แนวทางที่ดีกว่า**:

แทนที่จะไล่ตาม 100% coverage ควรมุ่งเน้น:

- **Risk-based Testing**: ทดสอบ critical paths และ high-risk scenarios ก่อน
- **Business-critical Scenarios**: ทดสอบ flows ที่ user ใช้บ่อยที่สุด
- **Known Problem Areas**: ทดสอบส่วนที่เคยมี bugs มาก่อน
- **Reasonable Target**: 80-90% coverage ถือว่าดีสำหรับ most projects, 99% ดีมากแล้ว

**สรุป**: 100% integration test coverage เป็นไปไม่ได้และไม่คุ้มค่าในทางปฏิบัติ แต่ควรมุ่งเน้นที่ coverage ของ critical paths และ high-risk areas ให้ดีกว่า ซึ่ง 99% ที่เราได้เป็นเป้าหมายที่ดีมากสำหรับระบบนี้

---

## ภาคผนวก: Test Commands

### รัน Tests

```bash
# Run all tests
pytest -v

# Run by marker
pytest -m bottomup -v
pytest -m topdown -v
pytest -m sandwich -v

# Quick run
pytest -q

# With coverage
pytest --cov=. --cov-report=html
```

### Project Structure

```
order-service-tests/
├── inventory.py (100% coverage)
├── payment.py (100% coverage)
├── shipping.py (100% coverage)
├── emailer.py (100% coverage)
├── order.py (100% coverage)
└── tests/
    ├── test_inventory_bottomup.py (10 tests)
    ├── test_payment_bottomup.py (9 tests)
    ├── test_shipping_bottomup.py (10 tests)
    ├── test_order_topdown.py (7 tests)
    └── test_order_sandwich.py (11 tests)

Total: 47 tests, 99% coverage
```
