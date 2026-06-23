import re
from urllib.parse import quote

WA_NUMBER = '5491155553333'

def generate_card_html(foto_base64, nombre, descripcion, precio_original, descuento):
    precio_original_int = int(precio_original)
    descuento_int = int(re.sub(r'[^0-9]', '', str(descuento)))
    precio_oferta = int(precio_original_int * (100 - descuento_int) / 100)
    badge = f'-{descuento_int}%'
    wa_msg = f'Hola! Quiero la oferta de {nombre} a ${precio_oferta:,}'
    wa_url = f'https://wa.me/{WA_NUMBER}?text={quote(wa_msg)}'

    return f'''        <!-- {nombre} -->
        <div class="offer-card reveal">
          <div class="offer-badge">{badge}</div>
          <img src="{foto_base64}" alt="{nombre}" class="offer-card-img" loading="lazy" />
          <div class="offer-card-body">
            <h3>{nombre}</h3>
            <p>{descripcion}</p>
            <div class="flex items-center gap-1 mb-3">
              <span class="old-price">${precio_original_int:,}</span>
              <span class="offer-price">${precio_oferta:,}</span>
            </div>
            <a href="{wa_url}" target="_blank" rel="noopener" class="btn-primary inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-semibold whatsapp-link">
              <i data-lucide="message-circle" class="w-4 h-4"></i>
              Consultar
            </a>
          </div>
        </div>'''

def insert_card_in_html(html, card_html):
    marker = '<div class="text-center mt-12 reveal">'
    last = html.rfind(marker)
    if last == -1:
        return html
    return html[:last] + card_html + '\n\n      ' + html[last:]

def update_index_html(html, todas_las_cards, max_cards=3):
    start_marker = '<div class="offer-grid">'
    end_marker = '</div>\n\n      <div class="text-center mt-10 reveal">'
    start = html.find(start_marker)
    end = html.find(end_marker, start)
    if start == -1 or end == -1:
        return html
    top_cards = '\n'.join(todas_las_cards[:max_cards])
    return html[:start + len(start_marker)] + '\n' + top_cards + '\n' + html[end:]
