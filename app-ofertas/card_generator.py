import re, time
from urllib.parse import quote

WA_NUMBER = '5491155553333'

def generate_card_html(foto_base64, nombre, descripcion, precio_original, descuento, fecha_vencimiento=''):
    precio_original_int = int(precio_original)
    descuento_int = int(re.sub(r'[^0-9]', '', str(descuento)))
    precio_oferta = int(precio_original_int * (100 - descuento_int) / 100)
    badge = f'-{descuento_int}%'
    wa_msg = f'¡Hola! Quiero la oferta de {nombre} a ${precio_oferta:,}'
    wa_url = f'https://wa.me/{WA_NUMBER}?text={quote(wa_msg)}'
    of_id = f"of_{int(time.time()*1000)}"

    venc_attr = f' data-vencimiento="{fecha_vencimiento}"' if fecha_vencimiento else ''

    html = f'''        <!-- {nombre} -->
        <div class="offer-card reveal" data-id="{of_id}"{venc_attr}>
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
    return of_id, html

def insert_card_in_html(html, card_html):
    marker = '<div class="text-center mt-12 reveal">'
    last = html.rfind(marker)
    if last == -1:
        return html
    return html[:last] + card_html + '\n\n      ' + html[last:]

def remove_card_by_id(html, card_id):
    """Remove an offer-card div with the given data-id."""
    start_marker = f'<div class="offer-card reveal" data-id="{card_id}"'
    start = html.find(start_marker)
    if start == -1:
        # Try with whitespace variation
        start = html.find(f'data-id="{card_id}"')
        if start == -1:
            return html, None
        # Find enclosing <div class="offer-card
        while start > 0:
            if html[start:start+25] == '<div class="offer-card' or html[start:start+20] == '<div class="offer-card':
                break
            start -= 1
        else:
            return html, None
    # Find the closing </div> of the offer-card
    # We need to count nested divs
    depth = 0
    i = start + 5  # past <div
    card_start = start
    
    # Find the comment line before the card (if any)
    comment_start = html.rfind('<!--', 0, start)
    if comment_start != -1 and html.find('-->', comment_start) > start:
        actual_start = comment_start
    else:
        actual_start = start
    
    while i < len(html):
        if html[i:i+4] == '<!--':
            endc = html.find('-->', i+4)
            if endc != -1:
                i = endc + 3
                continue
        if html[i:i+5] == '</div':
            # Check if this closes our card
            end = html.find('>', i)
            if end != -1:
                # Simple approach: find the nth </div> that's at the right depth
                pass
            break
        i += 1
    
    # Simpler approach: find </div> that ends the card's direct parent
    # Count opening divs from start
    search_from = card_start
    count = 0
    while search_from < len(html):
        tag_start = html.find('<div', search_from)
        if tag_start == -1 or tag_start > html.find('</div>', search_from):
            break
        search_from = tag_start + 4
        count += 1
    
    # Now find the closing </div> that matches
    close_count = 0
    search_from = card_start
    while search_from < len(html):
        div_close = html.find('</div>', search_from)
        if div_close == -1:
            return html, None
        close_count += 1
        if close_count == count:
            end = div_close + 6
            break
        search_from = div_close + 6
    else:
        return html, None
    
    removed = html[actual_start:end]
    result = html[:actual_start] + html[end:]
    return result, removed

def update_index_html(html, todas_las_cards, max_cards=3):
    start_marker = '<div class="offer-grid">'
    end_marker = '</div>\n\n      <div class="text-center mt-10 reveal">'
    start = html.find(start_marker)
    end = html.find(end_marker, start)
    if start == -1 or end == -1:
        return html
    top_cards = '\n'.join(todas_las_cards[:max_cards])
    return html[:start + len(start_marker)] + '\n' + top_cards + '\n' + html[end:]

EXPIRY_SCRIPT = '''
<style>
.offer-card.expirada { position: relative; }
.offer-card.expirada .offer-card-img { opacity: 0.5; }
.expirada-badge {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  background: #E63946; color: white; padding: 0.5rem 1.5rem;
  border-radius: 999px; font-weight: 800; font-size: 1.1rem;
  z-index: 10; white-space: nowrap; box-shadow: 0 4px 15px rgba(230,57,70,0.5);
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-50%,-50%) scale(1.05); } }
</style>
<script>
(function(){var d=document.querySelectorAll('[data-vencimiento]');d.forEach(function(e){var v=e.getAttribute('data-vencimiento');if(v&&new Date(v)<new Date()){e.classList.add('expirada');var b=document.createElement('div');b.className='expirada-badge';b.textContent='\\u26a0 OFERTA TERMINADA';e.appendChild(b);var i=e.querySelector('img');if(i)i.style.opacity='0.5'}})})()
</script>'''

def has_expiry_script(html):
    return 'expirada-badge' in html

def inject_expiry_script(html):
    if has_expiry_script(html):
        return html
    # Inject just before </body>
    body_end = html.rfind('</body>')
    if body_end == -1:
        return html + EXPIRY_SCRIPT
    return html[:body_end] + EXPIRY_SCRIPT + '\n' + html[body_end:]

def extract_card_by_id(html, card_id):
    """Extract a complete offer-card div by data-id."""
    start_marker = f'data-id="{card_id}"'
    start = html.find(start_marker)
    if start == -1:
        return None
    
    # Find the opening <div class="offer-card"
    while start > 0:
        if html[start:start+4] == '<div':
            break
        start -= 1
    if start == -1:
        return None
    
    # Find matching closing </div>
    depth = 0
    i = start
    first_div = True
    while i < len(html):
        if html[i:i+4] == '<!--':
            endc = html.find('-->', i+4)
            if endc != -1:
                i = endc + 3
                continue
        if html[i:i+5] == '</div':
            depth -= 1
            if depth == 0:
                end = html.find('>', i)
                return html[start:end+1]
            i += 5
            continue
        if html[i:i+4] == '<div' and not html[i+4].isalpha() and html[i+4] != ' ':
            depth += 1
            i += 4
            continue
        if html[i:i+4] == '<div' and (html[i+4] in ' \t\n\r>') and first_div:
            depth += 1
            first_div = False
            i += 4
            continue
        if html[i:i+2] == '</' and html[i+2] != 'd':
            i += 2
            continue
        i += 1
    return None
