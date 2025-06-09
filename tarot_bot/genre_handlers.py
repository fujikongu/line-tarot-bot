
from tarot_data import tarot_templates

def handle_genre_selection(genre):
    print(f"handle_genre_selection: genre = {genre}")  # デバッグ用出力
    template = tarot_templates.get(genre)
    if template:
        print(f"handle_genre_selection: template found for genre '{genre}'")
        return template
    else:
        print(f"handle_genre_selection: no template found for genre '{genre}'")
        return None
