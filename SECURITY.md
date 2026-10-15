# Security Policy

This policy explains how to report a security problem in KaliMCP, the MCP server that automates Kali Linux tools.

## Supported versions

Security fixes are made on the `main` branch. There are no versioned releases, so please test against the latest commit on `main`.

## Reporting a vulnerability

Please do not report a security problem in a public issue, discussion or pull request.

Report it privately with GitHub private vulnerability reporting: open the [Security tab](https://github.com/SiteQ8/KaliMCP/security) of this repository and choose **Report a vulnerability**. The report stays private between you and the maintainer until a fix is published.

A useful report includes:

- what the problem is and where it is (file, page, tool or endpoint)
- the steps to reproduce it
- the impact you expect
- the version or commit you tested

## What happens next

1. You receive an acknowledgement within 7 days.
2. The report is confirmed, or declined with the reason.
3. A confirmed problem is fixed on `main`, and a GitHub security advisory is published.
4. You are credited in the advisory unless you ask to stay anonymous.

## Scope

In scope:

- the MCP server in `scripts/kalimcp_server.py`
- how it handles input from MCP clients, for example a way to run a command or reach a file beyond what a tool is meant to do
- how credentials for SSH and remote sessions are handled
- the Docker test labs and the documentation site

Out of scope:

- denial of service and load testing
- social engineering
- automated scanner output without a demonstrated impact
- vulnerabilities in third party services or dependencies, which should be reported to their maintainers
- the offensive capability of the bundled Kali tools, which is the purpose of KaliMCP: use it only on systems you are authorized to test

<div dir="rtl">

## سياسة الأمن

نرحّب بالإبلاغ عن الثغرات الأمنية في KaliMCP ونتعامل مع كل بلاغ بسرية، لذا نرجو ألا تُنشر أي مشكلة أمنية في بلاغ عام أو نقاش أو طلب دمج، بل يُبلَّغ عنها عبر خاصية الإبلاغ الخاص عن الثغرات في GitHub بفتح [تبويب Security](https://github.com/SiteQ8/KaliMCP/security) في هذا المستودع واختيار Report a vulnerability، فيبقى البلاغ سريًا بينك وبين المشرف على المشروع حتى يُنشر الإصلاح.

يتضمن البلاغ المفيد وصف المشكلة وموضعها وخطوات إعادة إنتاجها وأثرها المتوقع والإصدار أو الإيداع الذي اختبرته، ثم يصلك إشعار بالاستلام خلال سبعة أيام، وبعد التحقق إما أن يُؤكَّد البلاغ وإما أن يُرفض مع بيان السبب، فإن تأكد عولجت المشكلة في الفرع الرئيسي ونُشرت نشرة أمنية في GitHub يُنسب فيها الفضل إليك ما لم تطلب عدم ذكر اسمك.

تُجرى الإصلاحات الأمنية على الفرع الرئيسي main ولا توجد إصدارات مرقّمة، لذا نرجو الاختبار على أحدث إيداع في الفرع الرئيسي.

ويشمل نطاق هذه السياسة خادم MCP في scripts/kalimcp_server.py وطريقة معالجته لمدخلات عملاء MCP كأن يُنفَّذ أمر أو يُوصَل إلى ملف خارج ما صُممت له الأداة وطريقة التعامل مع بيانات الدخول لجلسات SSH والجلسات البعيدة ومختبرات Docker التجريبية وموقع التوثيق، ولا يشمل هجمات حجب الخدمة واختبارات الحِمل ولا الهندسة الاجتماعية ولا نتائج أدوات الفحص الآلي التي لا يثبت لها أثر ولا ثغرات خدمات الطرف الثالث ومكتباته لأن الإبلاغ عنها يكون لدى القائمين عليها، ولا القدرات الهجومية لأدوات Kali المضمّنة لأنها الغاية من KaliMCP ولا يجوز استخدامها إلا على أنظمة لديك تصريح باختبارها.

</div>
