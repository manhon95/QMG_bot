import PIL
from PIL import Image
import os
import sqlite3


def drawmap(db, dst_dir):
    org_dir = os.getcwd()
    pic_dir = org_dir + '/pic/'
    mapimg = Image.open(pic_dir + 'map.png')
    #Uk victory
    uksupplyimg = Image.open(pic_dir + 'uk_supply.png')
    if db.execute("select location from card where cardid = 225;").fetchall()[0][0] == "played":
        mapimg.paste(uksupplyimg, (174-14, 130-15), uksupplyimg)
    if db.execute("select location from card where cardid = 226;").fetchall()[0][0] == "played":
        mapimg.paste(uksupplyimg, (649-14, 185-15), uksupplyimg)
    #Fr home/victory    
    frhomeimg = Image.open(pic_dir + 'fr_home.png')
    if (db.execute("select location from card where cardid = 222;").fetchall()[0][0] == "played") and (db.execute("select control from space where spaceid = 12;").fetchall()[0][0] == "Axis"):
        mapimg.paste(frhomeimg, (470-14, 172-15), frhomeimg)
    else:
        mapimg.paste(frhomeimg, (503-14, 264-15), frhomeimg)

    if db.execute("select location from card where cardid = 228;").fetchall()[0][0] == "played":
        frsupplyimg = Image.open(pic_dir + 'fr_supply.png')
        mapimg.paste(frsupplyimg, (576-14, 491-15), frsupplyimg)
    #Su home
    if db.execute("select location from card where cardid = 277;").fetchall()[0][0] == "played":
        suhomeimg = Image.open(pic_dir + 'su_home.png')
        sunohomeimg = Image.open(pic_dir + 'su_nohome.png')
        mapimg.paste(suhomeimg, (1002-14, 82-15), suhomeimg)
        mapimg.paste(sunohomeimg, (803-14, 170-15), sunohomeimg)
    #Ch home
    chhomeimg = Image.open(pic_dir + 'ch_home.png')
    if db.execute("select location from card where cardid = 345;").fetchall()[0][0] == "played":
        mapimg.paste(chhomeimg, (1009-14, 311-15), chhomeimg)
    else:
        mapimg.paste(chhomeimg, (1127-14, 316-15), chhomeimg)


        
    '''if db.execute("select location from card where cardid = 209;").fetchall()[0][0] == "played":
        usvictoryimg = Image.open('us_victory.png')
        usvictoryimg = usvictoryimg.resize((45, 39), Image.ANTIALIAS)
        mapimg.paste(usvictoryimg, (977, 290), usvictoryimg)'''
    geaimg = Image.open(pic_dir + 'ge_army.png')
    jpaimg = Image.open(pic_dir + 'jp_army.png')
    itaimg = Image.open(pic_dir + 'it_army.png')
    ukaimg = Image.open(pic_dir + 'uk_army.png')
    suaimg = Image.open(pic_dir + 'su_army.png')
    usaimg = Image.open(pic_dir + 'us_army.png')
    fraimg = Image.open(pic_dir + 'fr_army.png')
    chaimg = Image.open(pic_dir + 'ch_army.png')
    ukaimg = ukaimg.transpose(Image.FLIP_LEFT_RIGHT)
    suaimg = suaimg.transpose(Image.FLIP_LEFT_RIGHT)
    usaimg = usaimg.transpose(Image.FLIP_LEFT_RIGHT)
    fraimg = fraimg.transpose(Image.FLIP_LEFT_RIGHT)
    chaimg = chaimg.transpose(Image.FLIP_LEFT_RIGHT)
    genimg = Image.open(pic_dir + 'ge_navy.png')
    jpnimg = Image.open(pic_dir + 'jp_navy.png')
    itnimg = Image.open(pic_dir + 'it_navy.png')
    uknimg = Image.open(pic_dir + 'uk_navy.png')
    sunimg = Image.open(pic_dir + 'su_navy.png')
    usnimg = Image.open(pic_dir + 'us_navy.png')
    frnimg = Image.open(pic_dir + 'fr_navy.png')
    uknimg = uknimg.transpose(Image.FLIP_LEFT_RIGHT)
    sunimg = sunimg.transpose(Image.FLIP_LEFT_RIGHT)
    usnimg = usnimg.transpose(Image.FLIP_LEFT_RIGHT)
    frnimg = frnimg.transpose(Image.FLIP_LEFT_RIGHT)
    gefimg = Image.open(pic_dir + 'ge_air.png')
    jpfimg = Image.open(pic_dir + 'jp_air.png')
    itfimg = Image.open(pic_dir + 'it_air.png')
    ukfimg = Image.open(pic_dir + 'uk_air.png')
    sufimg = Image.open(pic_dir + 'su_air.png')
    usfimg = Image.open(pic_dir + 'us_air.png')
    frfimg = Image.open(pic_dir + 'fr_air.png')
    chfimg = Image.open(pic_dir + 'ch_air.png')
    gefimg = gefimg.rotate(-45)
    jpfimg = jpfimg.rotate(-45)
    itfimg = itfimg.rotate(-45)
    ukfimg = ukfimg.rotate(-45)
    sufimg = sufimg.rotate(-45)
    usfimg = usfimg.rotate(-45)
    frfimg = frfimg.rotate(-45)
    chfimg = chfimg.rotate(-45)
    width = gefimg.size[0]
    height = gefimg.size[1]
    gefimg = gefimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    jpfimg = jpfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    itfimg = itfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    ukfimg = ukfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    sufimg = sufimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    usfimg = usfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    frfimg = frfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    chfimg = chfimg.resize((int(width*2/3), int(height*2/3)), Image.ANTIALIAS)
    ukfimg = ukfimg.transpose(Image.FLIP_LEFT_RIGHT)
    sufimg = sufimg.transpose(Image.FLIP_LEFT_RIGHT)
    usfimg = usfimg.transpose(Image.FLIP_LEFT_RIGHT)
    frfimg = frfimg.transpose(Image.FLIP_LEFT_RIGHT)
    chfimg = chfimg.transpose(Image.FLIP_LEFT_RIGHT)
    army = {'ge':geaimg,'jp':jpaimg,'it':itaimg,'uk':ukaimg,'su':suaimg,'us':usaimg,'fr':fraimg,'ch':chaimg}
    navy = {'ge':genimg,'jp':jpnimg,'it':itnimg,'uk':uknimg,'su':sunimg,'us':usnimg,'fr':frnimg}
    air_force = {'ge':gefimg,'jp':jpfimg,'it':itfimg,'uk':ukfimg,'su':sufimg,'us':usfimg,'fr':frfimg,'ch':chfimg}
    land_list = db.execute("select distinct location from piece where type = 'army' and location != 'none';").fetchall()
    sea_list = db.execute("select distinct location from piece where type = 'navy' and location != 'none';").fetchall()
    air_list = db.execute("select distinct location from piece where type = 'air' and location != 'none';").fetchall()
    for land in land_list:
        piece_list = db.execute("select control from piece where type = 'army' and location = :space and control not in (select control from piece where type = 'air' and location = :space);", {'space':land[0]}).fetchall()
        posx = db.execute("select distinct posx from space where spaceid = :space;", {'space':land[0]}).fetchall()[0][0]-27
        posy = db.execute("select distinct posy from space where spaceid = :space;", {'space':land[0]}).fetchall()[0][0]-16
        for piece in piece_list:
            mapimg.paste(army[piece[0]], (posx, posy), army[piece[0]])
            posy -= 20
        if land in air_list:
            piece_list = db.execute("select control from piece where type = 'air' and location = :space;", {'space':land[0]}).fetchall()
            posx = db.execute("select distinct posx from space where spaceid = :space;", {'space':land[0]}).fetchall()[0][0]-20
            for piece in piece_list:
                mapimg.paste(air_force[piece[0]], (posx, posy), air_force[piece[0]])
                posy -= 20
    for sea in sea_list:
        piece_list = db.execute("select control from piece where type = 'navy' and location = :space and control not in (select control from piece where type = 'air' and location = :space);", {'space':sea[0]}).fetchall()
        posx = db.execute("select distinct posx from space where spaceid = :space;", {'space':sea[0]}).fetchall()[0][0]-35
        posy = db.execute("select distinct posy from space where spaceid = :space;", {'space':sea[0]}).fetchall()[0][0]-16
        for piece in piece_list:
            mapimg.paste(navy[piece[0]], (posx, posy), navy[piece[0]])
            posy += 20
        if sea in air_list:
            piece_list = db.execute("select control from piece where type = 'air' and location = :space;", {'space':sea[0]}).fetchall()
            posx = db.execute("select distinct posx from space where spaceid = :space;", {'space':sea[0]}).fetchall()[0][0]-20
            for piece in piece_list:
                mapimg.paste(air_force[piece[0]], (posx, posy), air_force[piece[0]])
                posy += 20



    pos = {'x':120, 'y':780}
    for country in ['ge', 'jp', 'it', 'uk', 'su', 'us', 'fr', 'ch']:
        remain_army_count = db.execute("select count(*) from piece where control = :country and type = 'army' and location = 'none';", {'country':country}).fetchall()[0][0]
        remain_navy_count = db.execute("select count(*) from piece where control = :country and type = 'navy' and location = 'none';", {'country':country}).fetchall()[0][0]
        remain_air_count = db.execute("select count(*) from piece where control = :country and type = 'air' and location = 'none';", {'country':country}).fetchall()[0][0]
        for i in range(remain_army_count):
            mapimg.paste(army[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS), (pos['x'], pos['y']), army[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS))
            pos['y'] -= 15
        for i in range(remain_navy_count):
            mapimg.paste(navy[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS), (pos['x'], pos['y']), navy[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS))
            pos['y'] -= 15
        for i in range(remain_air_count):
            mapimg.paste(air_force[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS), (pos['x'], pos['y']), air_force[country].resize((int(width*1/2), int(height*1/2)), Image.ANTIALIAS))
            pos['y'] -= 15
        pos['x'] += 30
        pos['y'] = 780
    
    mapimg.save(dst_dir + "/tmp.jpg", format="JPEG")
