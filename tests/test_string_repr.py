from rdsline.cli import to_string

def test_to_string():
    assert to_string({'stringValue': 'hello world'}) == 'hello world'
    assert to_string({'booleanValue': True}) == 'True'
    assert to_string({'longValue': 1}) == '1'
    assert to_string({'doubleValue': 1.0}) == '1.0'
    assert to_string({'blobValue': ''}) == 'BLOB'
    assert to_string({'arrayValue': ''}) == 'ARRAY'
    assert to_string({}) == 'UNKNOWN'
    assert to_string({'isNull': True}) == 'NULL'