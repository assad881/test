---
description: إدارة عميل AsaadStat — استقبال الطلب، تقدير السعر والمدة، عرض ورسالة رد
argument-hint: <client request text / files>
---
Handle this **AsaadStat** client request: $ARGUMENTS

1. Scope summary: level (undergrad/MSc/PhD/researcher), study type, deliverables requested, files
   received, what is missing (questionnaire? codebook? objectives?).
2. Work breakdown with hours: cleaning, coding, reliability, descriptive, inferential, regression,
   write-up, revisions.
3. Quote: use `assistant/knowledge/pricing.md` (OMR) — give a package price + optional add-ons.
4. Timeline with milestones.
5. Reply message ready to send (match the client's language; Arabic Gulf-professional tone),
   including what they must send and payment/revision terms.
6. Create `assistant/clients/<client-slug>/README.md` with the scope + status, and add a task to
   `assistant/TASKS.md`.
Academic integrity: AsaadStat analyses and explains; the student must understand and own their work.
