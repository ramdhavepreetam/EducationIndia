"""Import the vendor mock paper into a fresh scratch exam. Idempotent-ish: creates new rows."""
import asyncio, json, asyncpg, sys

import os
_HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(_HERE,'msce_class8_paper1_mock_2026.json')

# The vendor JSON carries bare filenames ("q71-stem.png"). They must be stored as
# ABSOLUTE urls: the frontend runs on a different origin (vite :5173) than the
# backend (:8000), so a relative "/static/..." path resolves against the frontend
# and returns index.html instead of the image — a broken-image icon on screen.
# This matches media/providers/local.py, which builds f"{BASE_URL}/static/{key}".
BASE_URL=os.environ.get('BASE_URL','http://localhost:8000')
IMG_PREFIX=f'{BASE_URL}/static/mock2026c8p1/'

def img(name):
    """Bare filename -> absolute served url. Passes through nulls and full urls."""
    if not name:
        return None
    if name.startswith(('http://','https://')):
        return name
    return IMG_PREFIX+name
url=[l.split('=',1)[1].strip() for l in open('.env') if l.startswith('DATABASE_URL=')][0].replace('postgresql+asyncpg://','postgresql://')

TOPICS={
 'English':['Reading Comprehension','Poetry','Advertisement Reading','Grammar','Vocabulary','Picture Comprehension'],
 'Mathematics':['Weights and Measures','Fractions','Profit and Loss','Simple Interest','Geometry','Percentages',
                'Time and Distance','Number System','Data Handling','Algebra','Calendar and Clock'],
}
SEC={'English':('I',1,25),'Mathematics':('II',26,75)}

async def main():
    d=json.load(open(SRC,encoding='utf-8'))
    paper=d['paper']
    c=await asyncpg.connect(url,statement_cache_size=0)
    async with c.transaction():
        board=await c.fetchval("select id from exam_boards order by id limit 1")
        cat  =await c.fetchval("select id from exam_categories order by id limit 1")
        ev=await c.fetchval("""insert into exam_events(board_id,category_id,title_en,title_mr,std_class,year,is_active)
             values($1,$2,$3,$4,$5,$6,false) returning id""",
             board,cat,'SCRATCH — Mock Test 2026 Std 8 Paper I (vendor import)','स्क्रॅच — सराव चाचणी २०२६ इयत्ता ८ पेपर १',
             paper['std_class'],paper['year'])
        exam=await c.fetchval("""insert into exams(event_id,paper_code,set_code,paper_number,title_en,title_mr,medium,
             total_questions,total_marks,marks_per_question,duration_minutes,is_active)
             values($1,$2,$3,1,$4,$5,'english',75,150,2,90,false) returning id""",
             ev,paper['paper_code'],'M26C8','Mock Test 2026 — Std 8 Paper I','सराव चाचणी २०२६ — इयत्ता ८ पेपर १')

        secid={}; topid={}
        for i,(name,(label,lo,hi)) in enumerate(SEC.items(),1):
            sid=await c.fetchval("""insert into sections(exam_id,section_label,subject_en,question_from,question_to,order_index)
                 values($1,$2,$3,$4,$5,$6) returning id""",exam,label,name,lo,hi,i)
            secid[name]=sid
            for j,t in enumerate(TOPICS[name],1):
                tid=await c.fetchval("insert into topics(section_id,name_en,order_index) values($1,$2,$3) returning id",sid,t,j)
                topid[(name,t)]=tid

        ctxid={}
        for i,ctx in enumerate(d['contexts']):
            cid=await c.fetchval("""insert into question_contexts(exam_id,context_type,title_en,title_mr,content_en,content_mr,
                 image_url,image_alt_en,image_alt_mr,instruction_en,instruction_mr,applies_from,applies_to,order_index)
                 values($1,$2::context_type,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14) returning id""",
                 exam,ctx['context_type'],ctx.get('title_en'),ctx.get('title_mr'),ctx.get('content_en'),ctx.get('content_mr'),
                 img(ctx.get('image')),ctx.get('image_alt_en'),ctx.get('image_alt_mr'),ctx.get('instruction_en'),
                 ctx.get('instruction_mr'),ctx.get('applies_from'),ctx.get('applies_to'),i+1)
            ctxid[i]=cid

        nq=0
        for q in d['questions']:
            sec=q['section']; 
            qid=await c.fetchval("""insert into questions(exam_id,section_id,topic_id,context_id,question_no,question_type,
                 text_en,text_mr,question_image_url,question_image_alt_en,question_image_alt_mr,
                 correct_option,correct_options,is_multi_select,is_cancelled,cancelled_reason,
                 explanation_en,explanation_mr,hint_en,hint_mr,marks,difficulty,tags)
                 values($1,$2,$3,$4,$5,$6::question_type,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,2,$21::difficulty_level,$22)
                 returning id""",
                 exam,secid[sec],topid[(sec,q['topic'])],ctxid.get(q.get('context_ref')) if q.get('context_ref') is not None else None,
                 q['question_no'],q['question_type'],q.get('text_en'),q.get('text_mr'),
                 img(q.get('question_image')),q.get('question_image_alt_en'),q.get('question_image_alt_mr'),
                 q.get('correct_option'),q.get('correct_options'),bool(q.get('is_multi_select',False)),
                 bool(q.get('is_cancelled',False)),q.get('cancelled_reason'),
                 q.get('explanation_en'),q.get('explanation_mr'),q.get('hint_en'),q.get('hint_mr'),
                 q.get('difficulty','medium'),q.get('tags') or [])
            for o in q['options']:
                await c.execute("""insert into options(question_id,option_no,text_en,text_mr,image_url,image_alt_en,image_alt_mr)
                     values($1,$2,$3,$4,$5,$6,$7)""",qid,o['option_no'],o.get('text_en'),o.get('text_mr'),
                     img(o.get('image')),o.get('image_alt_en'),o.get('image_alt_mr'))
            nq+=1
    print(f"event={ev} exam={exam} questions={nq} contexts={len(ctxid)}")
    h=await c.fetchrow("select * from v_paper_health where exam_id=$1",exam)
    print("health:",{k:h[k] for k in ('total_questions','missing_image_count','blank_correct_answer_count','publish_blocker_count')})
    await c.close()


if __name__ == "__main__":
    # Guarded: importing this module must never insert a duplicate exam.
    asyncio.run(main())
