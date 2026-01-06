# دليل ربط RAG بقاعدة البيانات PostgreSQL باستخدام Postman

## المتطلبات الأولية

1. ✅ التطبيق يعمل على `http://localhost:5000`
2. ✅ PostgreSQL يعمل على `localhost:5432`
3. ✅ MongoDB متصل (للحفظ)
4. ✅ Qdrant جاهز (للـ Vector Search)

---

## الخطوة 1: ربط قاعدة البيانات PostgreSQL

### Endpoint
```
POST http://localhost:5000/api/v1/data/connect-db/{project_id}
```

### الخطوات في Postman:

1. **أنشئ Request جديد**
   - Method: `POST`
   - URL: `http://localhost:5000/api/v1/data/connect-db/pos_system_project`
   - استبدل `pos_system_project` بأي اسم مشروع تريده

2. **في تبويب Headers**
   - Key: `Content-Type`
   - Value: `application/json`

3. **في تبويب Body**
   - اختر `raw`
   - اختر `JSON` من القائمة المنسدلة
   - الصق الكود التالي:

```json
{
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "postgres",
    "password": "ahmad-1234",
    "database": "pos_system_db"
}
```

4. **أرسل الطلب (Send)**
   - ✅ إذا نجح: ستحصل على `asset_id` في الرد
   - ❌ إذا فشل: تأكد من أن PostgreSQL يعمل والمعلومات صحيحة

### مثال على الاستجابة الناجحة:
```json
{
    "signal": "file_upload_success",
    "asset_id": "507f1f77bcf86cd799439011"
}
```

**⚠️ مهم: احفظ `asset_id` لأنك ستحتاجه في الخطوة التالية!**

---

## الخطوة 2: استخراج البيانات من قاعدة البيانات

### Endpoint
```
POST http://localhost:5000/api/v1/data/process-db/{project_id}
```

### الطريقة الأولى: استخراج من جداول محددة

#### الخطوات في Postman:

1. **أنشئ Request جديد**
   - Method: `POST`
   - URL: `http://localhost:5000/api/v1/data/process-db/pos_system_project`

2. **Headers**
   - Key: `Content-Type`
   - Value: `application/json`

3. **Body (JSON)**
```json
{
    "asset_id": "507f1f77bcf86cd799439011",
    "tables": ["users", "products", "orders"],
    "limit_per_table": 1000,
    "chunk_size": 200,
    "overlap_size": 30,
    "do_reset": 0
}
```

**المعاملات:**
- `asset_id`: استخدم الـ ID الذي حصلت عليه من الخطوة 1
- `tables`: قائمة أسماء الجداول التي تريد استخراجها
- `limit_per_table`: حد أقصى لعدد الصفوف من كل جدول (افتراضي: 1000)
- `chunk_size`: حجم كل مقطع نصي (افتراضي: 100)
- `overlap_size`: التداخل بين المقاطع (افتراضي: 20)
- `do_reset`: إذا كان `1` سيحذف كل الـ chunks القديمة للمشروع

### الطريقة الثانية: استخراج باستعلام SQL مخصص

استخدم نفس الـ Endpoint مع Body مختلف:

```json
{
    "asset_id": "507f1f77bcf86cd799439011",
    "custom_query": "SELECT * FROM users WHERE active = true",
    "chunk_size": 200,
    "overlap_size": 30,
    "do_reset": 0
}
```

**ملاحظة:** إذا استخدمت `custom_query`، لا حاجة لـ `tables`

### مثال على الاستجابة الناجحة:
```json
{
    "signal": "processing_success",
    "inserted_chunks": 145,
    "processed_files": 1
}
```

---

## الخطوة 3: فهرسة البيانات في Vector Database (Qdrant)

### Endpoint
```
POST http://localhost:5000/api/v1/nlp/index/push/{project_id}
```

#### الخطوات في Postman:

1. **أنشئ Request جديد**
   - Method: `POST`
   - URL: `http://localhost:5000/api/v1/nlp/index/push/pos_system_project`

2. **Headers**
   - Key: `Content-Type`
   - Value: `application/json`

3. **Body (JSON)**
```json
{
    "do_reset": 0
}
```

**المعاملات:**
- `do_reset`: إذا كان `1` سيحذف المجموعة القديمة في Qdrant وينشئ واحدة جديدة

### مثال على الاستجابة الناجحة:
```json
{
    "signal": "insert_into_vectordb_success",
    "inserted_items_count": 145
}
```

---

## الخطوة 4: التحقق من معلومات الفهرس (اختياري)

### Endpoint
```
GET http://localhost:5000/api/v1/nlp/index/info/{project_id}
```

#### الخطوات في Postman:

1. **أنشئ Request جديد**
   - Method: `GET`
   - URL: `http://localhost:5000/api/v1/nlp/index/info/pos_system_project`
   - لا حاجة لـ Body

### مثال على الاستجابة:
```json
{
    "signal": "vectordb_collection_retrieved",
    "collection_info": {
        "points_count": 145,
        ...
    }
}
```

---

## الخطوة 5: السؤال والحصول على إجابة من RAG

### Endpoint
```
POST http://localhost:5000/api/v1/nlp/index/answer/{project_id}
```

#### الخطوات في Postman:

1. **أنشئ Request جديد**
   - Method: `POST`
   - URL: `http://localhost:5000/api/v1/nlp/index/answer/pos_system_project`

2. **Headers**
   - Key: `Content-Type`
   - Value: `application/json`

3. **Body (JSON)**
```json
{
    "text": "كم عدد المستخدمين النشطين؟",
    "limit": 5
}
```

**المعاملات:**
- `text`: السؤال الذي تريد طرحه
- `limit`: عدد المستندات المطلوب استرجاعها من قاعدة المتجهات (افتراضي: 10)

### مثال على الاستجابة الناجحة:
```json
{
    "signal": "rag_answer_success",
    "answer": "بناءً على البيانات المتاحة، يوجد X مستخدم نشط...",
    "full_prompt": "...",
    "chat_history": [...]
}
```

---

## الخطوة 6: البحث في قاعدة المتجهات (اختياري)

يمكنك البحث مباشرة في قاعدة المتجهات بدون توليد إجابة:

### Endpoint
```
POST http://localhost:5000/api/v1/nlp/index/search/{project_id}
```

#### Body (JSON):
```json
{
    "text": "مستخدمين نشطين",
    "limit": 5
}
```

---

## ملخص الخطوات الكاملة

```
1. ربط قاعدة البيانات
   POST /api/v1/data/connect-db/{project_id}
   ↓ (احصل على asset_id)

2. استخراج ومعالجة البيانات
   POST /api/v1/data/process-db/{project_id}
   ↓ (حفظ في MongoDB كـ Chunks)

3. فهرسة في Vector DB
   POST /api/v1/nlp/index/push/{project_id}
   ↓ (إنشاء Embeddings وحفظ في Qdrant)

4. السؤال والحصول على إجابة
   POST /api/v1/nlp/index/answer/{project_id}
   ✅ (الإجابة النهائية)
```

---

## استكشاف الأخطاء

### خطأ في الاتصال بقاعدة البيانات:
- ✅ تأكد أن PostgreSQL يعمل
- ✅ تأكد من صحة `host`, `port`, `username`, `password`
- ✅ تأكد أن قاعدة البيانات `pos_system_db` موجودة

### خطأ في معالجة البيانات:
- ✅ تأكد من أسماء الجداول صحيحة
- ✅ تأكد أن الجداول تحتوي على بيانات
- ✅ تأكد من صحة استعلام SQL إذا استخدمته

### خطأ في الفهرسة:
- ✅ تأكد من وجود Chunks في MongoDB أولاً
- ✅ تأكد من إعدادات Embedding Model

### لا توجد إجابة من RAG:
- ✅ تأكد أن البيانات تم فهرستها في Qdrant
- ✅ جرب تغيير `limit` في طلب الإجابة
- ✅ تأكد من أن السؤال واضح ومحدد

---

## أمثلة إضافية

### مثال: استعلام مع JOIN
```json
{
    "asset_id": "507f1f77bcf86cd799439011",
    "custom_query": "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
    "chunk_size": 150,
    "overlap_size": 25,
    "do_reset": 1
}
```

### مثال: سؤال بالعربية
```json
{
    "text": "ما هي المنتجات الأكثر مبيعاً؟",
    "limit": 10
}
```

### مثال: سؤال بالإنجليزية
```json
{
    "text": "What are the most active users?",
    "limit": 5
}
```

---

## نصائح مهمة

1. **استخدم `do_reset: 1`** عند تحديث البيانات في قاعدة PostgreSQL لإعادة معالجة كل شيء
2. **`chunk_size` و `overlap_size`** يؤثران على جودة الإجابات - جرب قيم مختلفة
3. **`limit`** في البحث يؤثر على عدد المستندات المسترجعة - كلما زاد زادت التفاصيل
4. **احفظ `asset_id`** في مكان آمن لإعادة استخدامه

---

## Collection جاهز للاستيراد في Postman

يمكنك إنشاء Collection في Postman يحتوي على جميع الـ Requests أعلاه لتسهيل العمل.


