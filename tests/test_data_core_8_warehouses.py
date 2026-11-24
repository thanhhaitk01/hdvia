import os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from data_core import COLLECTIONS,schema,validate,LearningPipeline

def test_eight_domains_exist():
    assert len(COLLECTIONS)==8
    assert set(COLLECTIONS)==set(schema()['collections'])

def test_admin_record():
    r=validate('administrative',{'code':'01','slug':'ha-noi','name':'Thành phố Hà Nội','type':'thành phố','region':'Miền Bắc','effective_from':'2025-07-01'})
    assert r['code']=='01' and r['updated_at'].endswith('Z')

def test_destination_uses_province_code():
    r=validate('destinations',{'slug':'son-tra','name':'Sơn Trà','province_code':'48','type':'danh-thang','overview':'Bán đảo'})
    assert r['province_code']=='48'

def test_pipeline_does_not_auto_publish():
    p=LearningPipeline(); item=p.ingest(kind='knowledge',payload={'title':'x','place':'Huế','content':'Nội dung kiểm chứng đủ dài cho pipeline dữ liệu HDVIA.','source':'gov'},source='gov')
    assert item['status']=='CANDIDATE'
    assert p.validate(item)['status']=='VALIDATED'
    assert item['status']!='PUBLISHED'

def test_34_provinces_seeded():
    from data_core import seed
    rows=seed()['administrative']
    assert len(rows)==34
    assert len({r['code'] for r in rows})==34
