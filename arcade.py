import ezdxf

def create_arcade_final(filename):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Definisanje tačaka u formatu: (x, y, start_width, end_width, bulge)
    # x, y su koordinate u mm
    # bulge: 0 = ravno, >0 = luk ka spolja, <0 = luk ka unutra
    
    points = [
        (0, 0, 0, 0, 0),             # 0: Donji levi ugao (Base Start)
        (850, 0, 0, 0, 0),           # 1: Donji desni ugao (Base End)
        (850, 920, 0, 0, 0.15),      # 2: Uspon do kontrolnog panela (blagi luk ka spolja)
        (1050, 1050, 0, 0, 0),       # 3: Ivica kontrolnog panela (najisturenija tačka)
        (1050, 1180, 0, 0, -0.45),   # 4: Početak "grla" (veliki unutrašnji luk za ekran)
        (750, 1400, 0, 0, 0),        # 5: Kraj unutrašnjeg luka (iznad ekrana)
        (750, 1820, 0, 0, 0.25),     # 6: Ispod marquee-a (luk ka spolja za kapu)
        (900, 1920, 0, 0, 0),        # 7: Prednji vrh kape
        (900, 2000, 0, 0, 0),        # 8: NAJVIŠA TAČKA (2000mm)
        (0, 2000, 0, 0, 0)           # 9: Gornji levi ugao (leđa kabineta)
    ]

    # Kreiramo poliliniju direktno sa tačkama
    # close=True automatski spaja poslednju tačku (0,2000) sa prvom (0,0)
    msp.add_lwpolyline(points, close=True)

    doc.saveas(filename)
    print(f"Fajl '{filename}' je generisan. Visina: 2000mm.")

if __name__ == "__main__":
    create_arcade_final("arkadni_kabinet_200cm.dxf")