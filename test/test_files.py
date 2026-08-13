'''
test_files - test runningroutes.files
=========================================================
'''

# standard
from os.path import join, exists

# pypi
import pytest

# homegrown
from runningroutes.files import create_fidfile, get_fidfile
from runningroutes.models import db, LocalInterest
from loutilities.user.model import Interest


@pytest.fixture
def filesetup(bare_dbapp, tmp_path):
    bare_dbapp.config['APP_FILE_FOLDER'] = str(tmp_path / 'files')

    interest = Interest(interest='fsrc', description='FSRC')
    db.session.add(interest)
    db.session.commit()
    linterest = LocalInterest(interest_id=interest.id)
    db.session.add(linterest)
    db.session.commit()

    return {'app': bare_dbapp, 'interest': interest}


def test_create_fidfile_creates_group_folder_and_db_record(filesetup):
    fid, filepath = create_fidfile('fsrc', 'route.gpx', 'application/gpx+xml')

    assert exists(join(filesetup['app'].config['APP_FILE_FOLDER'], 'fsrc'))
    assert filepath == join(filesetup['app'].config['APP_FILE_FOLDER'], 'fsrc', fid)

    from runningroutes.models import Files
    file = Files.query.filter_by(fileid=fid).one()
    assert file.filename == 'route.gpx'
    assert file.mimetype == 'application/gpx+xml'
    assert file.interest.interest_id == filesetup['interest'].id


def test_create_fidfile_uses_supplied_fid(filesetup):
    fid, filepath = create_fidfile('fsrc', 'route.gpx', 'application/gpx+xml', fid='myfid')

    assert fid == 'myfid'
    assert filepath.endswith('myfid')


def test_create_fidfile_generates_unique_fids(filesetup):
    fid1, _ = create_fidfile('fsrc', 'route1.gpx', 'application/gpx+xml')
    fid2, _ = create_fidfile('fsrc', 'route2.gpx', 'application/gpx+xml')

    assert fid1 != fid2


def test_get_fidfile_reads_back_contents(filesetup):
    fid, filepath = create_fidfile('fsrc', 'route.gpx', 'application/gpx+xml')
    with open(filepath, 'w') as f:
        f.write('line1\n')
        f.write('line2\n')

    result = get_fidfile(fid)

    assert result['contents'] == ['line1\n', 'line2\n']
    assert result['group'].interest == 'fsrc'
