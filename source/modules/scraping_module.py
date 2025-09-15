# Váš soubor: source/modules/scraping_module.py

import asyncio
import os
import random
import logging
from datetime import timedelta
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from readability import Document
from bs4 import BeautifulSoup
from typing import List, Dict, Any

# Základní konfigurace logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def scrape_articles(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Funkce pro scrapování článků z poskytnutých URL adres.
    
    Args:
        urls: Seznam URL adres článků k obnažování
        
    Returns:
        Seznam slovníků s informacemi o článcích.
    """
    logging.info(f"Scraping started for {len(urls)} URLs.")
    
    # Seznam pro ukládání výsledků
    scraped_articles = []
    
    # ==============================================================================
    # ZMĚNA JE ZDE: Sjednocená a opravená konfigurace crawleru
    # ==============================================================================
    
    # 1. Vytvoříme crawler bez jakýchkoliv spouštěcích voleb, ty definujeme níže.
    crawler = PlaywrightCrawler(
        headless=True,
        request_handler_timeout=timedelta(seconds=120)
    )
    
    # 2. Všechny volby pro spuštění prohlížeče definujeme na JEDINÉM místě.
    crawler.browser_pool_options = {
        'stealth': True,
        'launch_options': {
            'args': [
                # Klíčové argumenty pro stabilní běh v Dockeru
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                
                # Vaše původní, zachované argumenty
                '--start-maximized', 
                '--disable-web-security', 
                '--disable-features=VizDisplayCompositor'
            ],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080}
        }
    }
    crawler.navigation_timeout_sec = 120
    
    # ==============================================================================
    # KONEC ZMĚN - ZBYTEK KÓDU JE VÁŠ PŮVODNÍ A JE V POŘÁDKU
    # ==============================================================================

    async def super_aggressive_cookie_handler(page, log):
        """Super agresivní handler pro cookie bannery - zkusí vše možné"""
        # ... (váš kód zde zůstává beze změny)
        log.info("🔍 Spouštím super agresivní cookie banner handler...")
        
        # Počkáme trochu déle na načtení
        await page.wait_for_timeout(5000)
        
        # ČT24 Specific Strategy: Přímé cílení na cookie banner
        log.info("Strategy ČT24: Hledám specifické ČT24 cookie elementy...")
        try:
            ct24_selectors = [
                '#cc-main', '.cm-wrapper', '[class*="cookie"]', '[class*="consent"]',
                '[data-nosnippet]', '#cm__desc', '.cc--anim',
                'button:contains("Přijmout")', 'button:contains("Accept")',
                'button:contains("Souhlasím")', 'button:contains("OK")'
            ]
            
            for selector in ct24_selectors:
                try:
                    # Zkusíme najít a kliknout na cookie tlačítko
                    elements = page.locator(selector)
                    count = await elements.count()
                    if count > 0:
                        log.info(f"🎯 Našel jsem ČT24 cookie element: {selector}")
                        for i in range(min(count, 3)):
                            try:
                                element = elements.nth(i)
                                if await element.is_visible():
                                    text = await element.inner_text() if await element.inner_text() else ""
                                    if any(word in text.lower() for word in ['přijmout', 'accept', 'souhlasím', 'ok']) or 'button' in selector:
                                        await element.click(timeout=3000)
                                        await page.wait_for_timeout(2000)
                                        log.info(f"✅ Klikl jsem na ČT24 cookie tlačítko: {text[:50]}")
                                        return True
                            except Exception as e:
                                log.debug(f"ČT24 element {i} click failed: {e}")
                                continue
                except Exception as e:
                    log.debug(f"ČT24 selector {selector} failed: {e}")
                    continue
                    
            # Zkusíme najít tlačítka přímo podle textu
            text_selectors = [
                'text=Přijmout', 'text=Accept', 'text=Souhlasím', 'text=OK',
                'text=Povolit vše', 'text=Allow all', 'text=Zavřít'
            ]
            
            for text_selector in text_selectors:
                try:
                    element = page.locator(text_selector).first
                    if await element.is_visible():
                        await element.click(timeout=3000)
                        await page.wait_for_timeout(2000)
                        log.info(f"✅ Klikl jsem na ČT24 text tlačítko: {text_selector}")
                        return True
                except Exception as e:
                    log.debug(f"ČT24 text selector {text_selector} failed: {e}")
                    continue
                    
        except Exception as e:
            log.error(f"ČT24 strategy failed: {e}")
        
        # Strategy 1: Keypress Escape (často zavře modaly)
        log.info("Strategis 1: Zkouším Escape klávesy...")
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(2000)
        except Exception as e:
            log.debug(f"Escape nefungoval: {e}")
        
        # Strategy 2: Hledáme jakékoliv tlačítko obsahující klíčová slova (s vylepšeným filtrováním)
        log.info("Strategy 2: Hledám všechna tlačítka s relevantním textem...")
        try:
            # Získáme všechny interaktivní elementy (omezíme počet pro rychlost)
            interactive_elements = await page.locator('button, [role="button"], a, input[type="button"], input[type="submit"]').all()
            
            # Omezíme na prvních 50 elementů aby se nezacyklilo
            max_elements = min(50, len(interactive_elements))
            log.info(f"Nalezeno {len(interactive_elements)} interaktivních elementů, testuju prvních {max_elements}")
            
            for i, element in enumerate(interactive_elements[:max_elements]):
                try:
                    if await element.is_visible():
                        text = (await element.inner_text()).lower().strip()
                        aria_label = await element.get_attribute('aria-label') or ""
                        title = await element.get_attribute('title') or ""
                        full_text = f"{text} {aria_label.lower()} {title.lower()}"
                        
                        # Přeskočíme příliš dlouhé texty (pravděpodobně články)
                        if len(text) > 200:
                            log.debug(f"Přeskakuji element {i}: příliš dlouhý text ({len(text)} znaků)")
                            continue
                        
                        # Klíčová slova pro consent (rozšířeno pro iROZHLAS a další)
                        consent_keywords = [
                            'přijmout', 'souhlasím', 'accept', 'agree', 'ok', 'ano', 'yes',
                            'pokračovat', 'continue', 'zavřít', 'close', 'dismiss',
                            'všechno', 'vše', 'all', 'hotovo', 'done',
                            # iROZHLAS specifické
                            'rozumím', 'souhlasit', 'cookies', 'soubory cookies',
                            'personalizace', 'reklama', 'analytics',
                            'uložit volby', 'uložit nastavení', 'potvrdit',
                            'přijmout vše', 'přijmout všechny', 'povolit vše',
                            # Anglické varianty
                            'allow all', 'accept all', 'save preferences',
                            'i understand', 'got it', 'confirm'
                        ]
                        
                        # Vyloučíme jména a navigační prvky + ČT24 specifické
                        excluded_keywords = [
                            'kaja kallasová', 'kallasová', 'redaktor', 'autor',
                            'články', 'zprávy', 'tag', 'archiv', 'seznam',
                            'více článků', 'další články', 'související',
                            # ČT24 specifické - názvy článků a časové údaje
                            'před', 'hodinou', 'hodinami', 'minutami', 'dnem', 'dny',
                            'jáchymovský', 'potok', 'karlovarsku', 'znečistila',
                            'kyjev', 'moskva', 'podle', 'médií', 'přiznal', 'útok',
                            'železnici', 'mrtvých', 'mluví', 'ruskou', 'uhynuly',
                            'desítky', 'ryb', 'neznámá', 'látka'
                        ]
                        
                        # Kontrola, zda text obsahuje consent klíčová slova, ale ne vyloučené
                        has_consent = any(keyword in full_text for keyword in consent_keywords)
                        has_excluded = any(excluded in full_text for excluded in excluded_keywords)
                        
                        if has_consent and not has_excluded:
                            log.info(f"🎯 Našel jsem podezřelé CONSENT tlačítko: '{text}' (aria: '{aria_label}', title: '{title}')")
                            
                            # Zkusíme kliknout s timeout
                            await element.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)
                            await element.click(timeout=5000)  # Přidán timeout
                            await page.wait_for_timeout(3000)
                            
                            # Zkontrolujeme úspěch
                            new_content = await page.content()
                            if len(new_content) != len(await page.content()) or "souhlas" not in new_content.lower()[:2000]:
                                log.info(f"✅ Úspěch s consent tlačítkem: {text}")
                                return True
                        elif has_excluded:
                            log.debug(f"⚠️ Přeskočeno vyloučené tlačítko: '{text[:50]}' (obsahuje vyloučené klíčové slovo)")
                            
                except Exception as e:
                    log.debug(f"Chyba s tlačítkem {i}: {e}")
                    continue
                    
        except Exception as e:
            log.error(f"Strategy 2 selhala: {e}")
        
        # Strategy 3: Agresivní JavaScript injection (vylepšeno pro ČT24)
        log.info("Strategy 3: JavaScript injection pro odstranění overlay...")
        try:
            js_code = '''
            // ČT24 specifické selektory
            const ct24Selectors = [
                '#cc-main', '.cm-wrapper', '[data-nosnippet]', 
                '[class*="cc--"]', '[class*="cm__"]'
            ];
            
            // Obecné overlay selektory
            const overlaySelectors = [
                '[class*="overlay"]', '[class*="modal"]', '[class*="popup"]', 
                '[class*="consent"]', '[class*="cookie"]', '[class*="gdpr"]',
                '[style*="position: fixed"]', '[style*="z-index"]'
            ];
            
            let removed = 0;
            
            // Nejdříve specifické ČT24 elementy
            ct24Selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.display = 'none';
                    el.remove();
                    removed++;
                });
            });
            
            // Pak obecné overlay elementy
            overlaySelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    if (el.offsetHeight > 100 && el.offsetWidth > 100) {
                        el.style.display = 'none';
                        removed++;
                    }
                });
            });
            
            // Obnovíme scrollování na body
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            
            // Odstraníme pointer-events blocking
            document.querySelectorAll('*').forEach(el => {
                if (el.style.pointerEvents === 'none') {
                    el.style.pointerEvents = 'auto';
                }
            });
            
            return removed;
            '''
            
            removed_count = await page.evaluate(js_code)
            if removed_count > 0:
                log.info(f"✅ JavaScript odstranil {removed_count} overlay elementů!")
                await page.wait_for_timeout(2000)
                return True
                
        except Exception as e:
            log.error(f"JavaScript injection selhala: {e}")
        
        # Strategy 4: Simulace TAB + ENTER navigace
        log.info("Strategy 4: TAB navigace pro nalezení consent tlačítka...")
        try:
            for i in range(20):  # Zkusíme až 20 TAB kroků
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(200)
                
                # Zkusíme ENTER na aktuální element
                focused_element = await page.evaluate('document.activeElement')
                if focused_element:
                    try:
                        text = await page.evaluate('document.activeElement.innerText || document.activeElement.value || ""')
                        if any(word in text.lower() for word in ['přijmout', 'souhlasím', 'accept', 'ok']):
                            log.info(f"🎯 Našel jsem focused element s textem: {text}")
                            await page.keyboard.press('Enter')
                            await page.wait_for_timeout(3000)
                            
                            # Zkontrolujeme úspěch
                            new_content = await page.content()
                            if "souhlas" not in new_content.lower()[:2000]:
                                log.info("✅ TAB+ENTER strategie úspěšná!")
                                return True
                    except:
                        continue
                        
        except Exception as e:
            log.error(f"TAB strategie selhala: {e}")
        
        # Strategy 5: Brute force click na největší elementy ve středu stránky
        log.info("Strategy 5: Brute force klikání na velké elementy...")
        try:
            # Najdeme velké elementy, které by mohly být consent dialog
            large_elements = await page.evaluate('''
                Array.from(document.querySelectorAll('*')).filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 300 && rect.height > 200 && 
                           rect.top < window.innerHeight && rect.left < window.innerWidth;
                }).slice(0, 10);
            ''')
            
            for i in range(min(5, len(large_elements))):  # Max 5 pokusů
                try:
                    # Klikneme do středu elementu
                    await page.click(f'xpath=//*[position()={i+1}]', timeout=2000)
                    await page.wait_for_timeout(2000)
                    
                    # Zkontrolujeme úspěch
                    new_content = await page.content()
                    if "souhlas" not in new_content.lower()[:2000]:
                        log.info(f"✅ Brute force click #{i+1} úspěšný!")
                        return True
                        
                except Exception as e:
                    log.debug(f"Brute force click #{i+1} selhal: {e}")
                    continue
                    
        except Exception as e:
            log.error(f"Brute force strategie selhala: {e}")
        
        log.error("🚫 Všechny strategie selhaly - cookie banner se nepodařilo zavřít")
        return False

    @crawler.pre_navigation_hook
    async def handle_consent(context: PlaywrightCrawlingContext):
        # ... (váš kód zde zůstává beze změny)
        url = context.request.url
        log = context.log

        log.info(f"Pre-navigation hook pro: {url}")
        
        try:
            # Počkáme na základní načtení stránky
            await context.page.wait_for_load_state('domcontentloaded', timeout=15000)
            
            # Ověříme, že jsme skutečně na cílové stránce
            current_url = context.page.url
            if "about:blank" in current_url or not current_url.startswith("http"):
                log.info("Stránka ještě není načtená, přeskakujem pre-navigation hook")
                return
            
            log.info(f"✅ Stránka načtena: {current_url}")
            
            # Screenshot před pokusem (pouze pokud existuje screenshots složka)
            if os.path.exists("screenshots"):
                before_path = f"screenshots/before_consent_{random.randint(1000, 9999)}.png"
                await context.page.screenshot(path=before_path, full_page=True)
                log.info(f"Screenshot před: {before_path}")
            
            # Simulujeme lidské chování
            await context.page.mouse.wheel(0, random.randint(50, 150))
            await context.page.wait_for_timeout(random.randint(2000, 4000))
            
            # Zavoláme super agresivní handler
            success = await super_aggressive_cookie_handler(context.page, log)
            
            # Screenshot po pokusu (pouze pokud existuje screenshots složka)
            if os.path.exists("screenshots"):
                after_path = f"screenshots/after_consent_{random.randint(1000, 9999)}.png"
                await context.page.screenshot(path=after_path, full_page=True)
                log.info(f"Screenshot po: {after_path}")
            
            if success:
                log.info("🎉 Banner úspěšně uzavřen!")
                await context.page.wait_for_load_state('domcontentloaded', timeout=10000)
                await context.page.wait_for_timeout(3000)
            else:
                log.error("😞 Všechny pokusy o uzavření banneru selhaly")
                
        except Exception as e:
            logging.exception("An error occurred in the pre_navigation_hook.")
            if os.path.exists("screenshots"):
                path = f"screenshots/pre_navigation_error_{random.randint(1000, 9999)}.png"
                await context.page.screenshot(path=path, full_page=True)
                log.error(f"Chyba v pre-navigation hook: {e}. Screenshot: {path}")
            else:
                log.error(f"Chyba v pre-navigation hook: {e}")

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        # ... (váš kód zde zůstává beze změny)
        log, page, request = context.log, context.page, context.request
        log.info(f"Zpracovávám: {request.url} - Titulek: {await page.title()}")

        try:
            await page.wait_for_load_state('networkidle', timeout=20000)
            log.info("Stránka je plně načtena")
            
            # Ještě jeden pokus o zavření bannerů
            await super_aggressive_cookie_handler(page, log)
            
            # Simulujeme čtení stránky
            for _ in range(random.randint(2, 4)):
                await page.mouse.wheel(0, random.randint(400, 800))
                await page.wait_for_timeout(random.randint(300, 1000))
                
        except Exception as e:
            logging.exception("An error occurred during page load wait or scroll.")
            log.warning(f"Chyba při čekání nebo scrollování: {e}")

        # Získáme obsah stránky
        html_content = await page.content()
        
        # Kontrola, zda jsme nebyli přesměrováni na jinou stránku
        current_url = page.url
        original_url = request.url
        
        if current_url != original_url:
            log.warning(f"🚨 DETEKOVÁNA REDIRECTA!")
            log.warning(f"   Původní URL: {original_url}")
            log.warning(f"   Aktuální URL: {current_url}")
            
            # Kontrola, zda jsme na seznamu článků místo konkrétního článku
            if any(keyword in current_url.lower() for keyword in ['autor', 'redaktor', 'seznam', 'archiv', 'tag']):
                log.error(f"❌ Přesměrováno na seznam článků místo konkrétního článku!")
                
                # Pokus o návrat na původní URL
                try:
                    log.info("🔄 Pokouším se vrátit na původní článek...")
                    await page.goto(original_url, wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    
                    # Kontrola, jestli jsme na správné stránce
                    current_url_after_return = page.url
                    if original_url in current_url_after_return:
                        log.info("✅ Úspěšně načten původní článek")
                        # Aktualizujeme HTML content
                        html_content = await page.content()
                    else:
                        log.error(f"❌ Návrat neúspěšný, stále na: {current_url_after_return}")
                        # Zkusíme ještě jednou s přímým přechodem
                        await page.goto(original_url, wait_until='domcontentloaded')
                        await page.wait_for_timeout(5000)
                        html_content = await page.content()
                        log.info("🔄 Zkusil jsem přímý přechod na článek")
                    
                except Exception as e:
                    log.error(f"❌ Nepodařilo se vrátit na původní článek: {e}")
        
        # Finální screenshot (pouze pokud existuje screenshots složka)
        if os.path.exists("screenshots"):
            final_path = f"screenshots/final_page_{random.randint(1000, 9999)}.png"
            await page.screenshot(path=final_path, full_page=True)
            log.info(f"Finální screenshot: {final_path}")
        
        # Zpracujeme obsah pomocí readability
        doc = Document(html_content)
        cleaned_title = doc.title()
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        cleaned_text = soup.get_text(separator=' ', strip=True)
        
        # Pokusíme se najít a přidat intro/lead paragraph, který může být mimo readability
        try:
            full_soup = BeautifulSoup(html_content, 'html.parser')
            
            # Nejdříve odstraníme sekce s doporučenými články
            unwanted_sections = [
                # iROZHLAS specifické sekce
                '.b-recommendations, .recommendations',
                '.b-related, .related, .related-articles',
                '.b-mostread, .mostread, .nejctenejsi',
                '.b-footer, .footer',
                '.b-navigation, .navigation',
                '.b-tags, .tags',
                
                # Obecné sekce s doporučenými články
                '[class*="recommend"], [class*="related"], [class*="suggest"]',
                '[class*="mostread"], [class*="popular"], [class*="nejcten"]',
                '[class*="footer"], [class*="navigation"], [class*="menu"]',
                '[class*="sidebar"], [class*="aside"]',
                
                # Specifické texty v iROZHLAS
                '*:contains("Zprávy, které jste nečetli")',
                '*:contains("Související články")',
                '*:contains("Další články")',
                '*:contains("Nejčtenější")',
                '*:contains("Mohlo by vás zajímat")',
                '*:contains("Doporučujeme")',
                '*:contains("Aktuální témata")',
                '*:contains("Sledujte nás")'
            ]
            
            # Odstraníme nežádoucí sekce
            for selector in unwanted_sections:
                try:
                    elements = full_soup.select(selector)
                    for element in elements:
                        element.decompose()
                except:
                    continue
            
            # Selektory pro intro/lead paragrafy (často mají speciální styling)
            intro_selectors = [
                # Specifický selektor pro aktuálně testovaný portál
                'div.opener, .opener, [class*="opener"]',
                '[itemprop="description"], [itemprop="summary"]',
                'div.opener[itemprop="description"]',  # Kombinace obou
                
                # Microdata a structured data selektory
                '[itemprop="description"], [itemprop="abstract"], [itemprop="summary"]',
                '[property="description"], [property="og:description"]',
                '[name="description"]',
                
                # Běžné třídy pro intro/lead paragrafy
                '.lead, .intro, .summary, .excerpt, .perex',
                '.article-lead, .article-intro, .article-summary',
                '.post-lead, .post-intro, .post-summary',
                '.lede, .standfirst, .abstract, .teaser',
                '[class*="lead"], [class*="intro"], [class*="perex"]',
                '[class*="summary"], [class*="excerpt"], [class*="abstract"]',
                
                # Strukturální selektory - první paragraf po nadpisu
                'h1 + p, h1 + div, h2 + p, h2 + div',
                '.title + p, .title + div, .headline + p, .headline + div',
                'header + p, header + div, .header + p, .header + div',
                '.article-header + p, .article-header + div',
                '.post-header + p, .post-header + div',
                
                # První paragraf/div v článku/main content
                'article > p:first-of-type, article > div:first-of-type',
                'main > p:first-of-type, main > div:first-of-type',
                '.article-content > p:first-of-type, .article-content > div:first-of-type',
                '.content > p:first-of-type, .content > div:first-of-type',
                
                # Paragrafy s typickými třídami pro intro
                'p.lead, p.intro, p.summary, p.excerpt, p.perex',
                'div.lead, div.intro, div.summary, div.excerpt, div.perex',
                'p[class*="lead"], p[class*="intro"], p[class*="summary"]',
                'div[class*="lead"], div[class*="intro"], div[class*="summary"]'
            ]
            
            intro_text = ""
            found_intros = set()  # Aby se nepřidaly duplicity
            
            for selector in intro_selectors:
                try:
                    elements = full_soup.select(selector)
                    for element in elements[:3]:  # Max 3 elementy per selector
                        if element.get_text(strip=True):
                            text = element.get_text(separator=' ', strip=True)
                            # Kontrola, zda tento text už nemáme
                            if len(text) > 30 and text not in found_intros:  # Sníženo z 50 na 30 znaků
                                # Filtrujeme text obsahující doporučené články
                                if not any(phrase in text.lower() for phrase in [
                                    'zprávy, které jste nečetli', 'související články', 'další články',
                                    'nejčtenější', 'mohlo by vás zajímat', 'doporučujeme',
                                    'sledujte nás', 'aktuální témata'
                                ]):
                                    found_intros.add(text)
                                    intro_text += text + " "
                                    log.info(f"✅ Našel jsem intro paragraph pomocí: '{selector}' (délka: {len(text)} znaků)")
                except Exception as e:
                    log.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Pokud jsme našli intro text, přidáme ho na začátek
            if intro_text.strip():
                # Kontrola, zda intro text už není v cleaned_text
                intro_clean = intro_text.strip()
                if intro_clean not in cleaned_text:
                    cleaned_text = intro_clean + " " + cleaned_text
                    log.info(f"🎯 Přidal jsem intro paragraph ({len(intro_clean)} znaků)")
                else:
                    log.info("ℹ️ Intro paragraph už je součástí hlavního textu")
            
        except Exception as e:
            log.warning(f"⚠️ Chyba při hledání intro paragraphu: {e}")
        
        # Dodatečné čištění textu od doporučených článků
        lines = cleaned_text.split('\n')
        cleaned_lines = []
        skip_section = False
        
        for line in lines:
            line_lower = line.strip().lower()
            
            # Detekce začátků sekcí s doporučenými články
            if any(phrase in line_lower for phrase in [
                'zprávy, které jste nečetli', 'související články', 'další články',
                'nejčtenější za posledních', 'nejčtenější za poslední',
                'mohlo by vás zajímat', 'doporučujeme', 'sledujte nás na',
                'aktuální témata', 'kde se nacházíte'
            ]):
                skip_section = True
                continue
                
            # Resetování při novém hlavním obsahu
            if not skip_section or (len(line.strip()) > 100 and not any(phrase in line_lower for phrase in [
                'články', 'zprávy', 'nejčtenější', 'mohlo by', 'doporučujeme'
            ])):
                skip_section = False
                
            if not skip_section:
                cleaned_lines.append(line)
        
        # Sloučíme vyčištěné řádky
        if len(cleaned_lines) < len(lines) * 0.8:  # Pokud jsme odstranili více než 20%
            cleaned_text = '\n'.join(cleaned_lines)
            log.info(f"🧹 Odstranil jsem doporučené články (z {len(lines)} na {len(cleaned_lines)} řádků)")
        else:
            log.info("ℹ️ Nebyly detekovány sekce s doporučenými články k odstranění")
        
        # Detailnější kontrola kvality a typu stránky
        suspicious_words = ['souhlas', 'cookie', 'consent', 'gdpr', 'reklama']
        suspicious_count = sum(1 for word in suspicious_words if word in cleaned_text.lower())
        
        # Kontrola, zda nejsme na seznamu článků místo konkrétního článku
        list_indicators = [
            'v textech na', 'články autora', 'další články', 'archiv článků',
            'zprávy ze světa', 'další zprávy', 'souvisejících článků',
            'více článků od', 'ostatní články', 'seznam článků',
            'kaja kallasová v textech', 'články redaktora',  # iROZHLAS specifické
            'články podle tagu', 'zprávy s tagem'
        ]
        list_count = sum(1 for indicator in list_indicators if indicator in cleaned_text.lower())
        
        # Detekce opakujících se vzorů (typické pro seznamy)
        lines = cleaned_text.split('\n')
        short_lines = [line.strip() for line in lines if 10 < len(line.strip()) < 100]
        if len(short_lines) > 20:  # Příliš mnoho krátkých řádků = seznam
            list_count += 2
            
        log.info(f"Kvalita extrakce: délka={len(cleaned_text)}, podezřelá slova={suspicious_count}, seznamové indikátory={list_count}")
        
        # Rozšířená kontrola problémů
        is_problematic = (
            len(cleaned_text) < 500 or 
            suspicious_count > 10 or 
            list_count > 3 or
            cleaned_text.count('|') > 20  # Mnoho | značí seznam
        )
        
        if is_problematic:
            if list_count > 3:
                log.warning("🚨 DETEKOVÁN SEZNAM ČLÁNKŮ místo konkrétního článku!")
            else:
                log.warning("🚨 Podezřelá kvalita extrakce - pravděpodobně stále consent dialog")
            
            # Zkusíme alternativní extrakci přímo z DOM
            try:
                # Pokusíme se najít hlavní obsah článku (rozšířeno pro iROZHLAS)
                article_selectors = [
                    # iROZHLAS specifické selektory
                    '.b-article__content, .article__content, .content__article',
                    '.b-article__text, .article__text, .text__article',
                    '.b-detail__content, .detail__content',
                    '[data-content="article"], [data-type="article"]',
                    
                    # Portal-specifické selektory na začátek (nejvyšší priorita)
                    'div.opener, .opener[itemprop="description"]',
                    '[itemprop="description"], [itemprop="summary"], [itemprop="abstract"]',
                    
                    # Hlavní content selektory
                    'article .text, article .content, article .body',
                    '.article-text, .article-content, .article-body',
                    '.post-text, .post-content, .post-body',
                    'main .text, main .content',
                    
                    # Obecné selektory pro články
                    'article, main, .article, .post, .content',
                    '[class*="article"] p, [class*="content"] p',
                    '.content p, main p',
                    
                    # Specifické selektory pro intro + content
                    '.lead, .intro, .perex, .summary, .excerpt',
                    'h1 + p, h1 + div, h2 + p, h2 + div, .title + p, .title + div'
                ]
                
                best_text = cleaned_text
                for selector in article_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            alt_text = ""
                            for element in elements[:15]:  # Zvýšeno z 10 na 15 elementů
                                try:
                                    text = await element.inner_text()
                                    # Vyfiltrujeme krátké texty (pravděpodobně navigace/menu)
                                    if len(text.strip()) > 30:  # Min 30 znaků
                                        alt_text += text + " "
                                except:
                                    continue
                            
                            # Kontrola kvality alternativního textu
                            alt_suspicious = sum(1 for word in suspicious_words if word in alt_text.lower())
                            if len(alt_text) > len(best_text) and alt_suspicious < 5:
                                best_text = alt_text.strip()
                                log.info(f"✅ Lepší text nalezen pomocí selektoru: {selector} (délka: {len(best_text)})")
                                break
                    except:
                        continue
                        
                cleaned_text = best_text
                
            except Exception as e:
                log.error(f"Alternativní extrakce selhala: {e}")
        
        # Přidáme výsledek do seznamu místo ukládání do JSON
        article_data = {
            'url': request.url,
            'final_url': page.url,  # URL kde jsme skončili
            'title': cleaned_title,
            'scraped_text': cleaned_text,
            'text_length': len(cleaned_text),
            'quality_score': f"suspicious_words: {suspicious_count}, list_indicators: {list_count}",
            'was_redirected': request.url != page.url
        }
        
        # Místo context.push_data přidáme do našeho seznamu
        scraped_articles.append(article_data)
        
        log.info(f"📄 Článek '{cleaned_title}' zpracován. Délka: {len(cleaned_text)} znaků, podezřelá slova: {suspicious_count}")

    # Spustíme crawler s poskytnutými URL
    await crawler.run(urls)
    
    # Vrátíme seznam scrapnutých článků
    return scraped_articles


# Příklad použití funkce (zůstává stejný)
async def example_usage():
    # ... (váš kód zde zůstává beze změny)
    """Příklad jak používat funkci scrape_articles"""
    
    # Seznam URL pro testování
    test_urls = [
        "https://www.ceskenoviny.cz/zpravy/soud-bude-rozhodovat-o-propusteni-nejdele-vezneneho-cecha/2720702",
        # Můžete přidat další URL zde
    ]
    
    try:
        # Vytvoříme screenshots složku pokud neexistuje
        os.makedirs("screenshots", exist_ok=True)
        
        # Spustíme scrapování
        print("🚀 Spouštím scrapování článků...")
        articles = await scrape_articles(test_urls)
        
        # Výpis výsledků
        print(f"\n✅ Úspěšně scrapnuto {len(articles)} článků:")
        for i, article in enumerate(articles, 1):
            print(f"\n📰 Článek {i}:")
            print(f"   URL: {article['url']}")
            print(f"   Titulek: {article['title']}")
            print(f"   Délka textu: {article['text_length']} znaků")
            print(f"   Kvalita: {article['quality_score']}")
            print(f"   Redirect: {'Ano' if article['was_redirected'] else 'Ne'}")
            print(f"   Text (náhled): {article['scraped_text'][:200]}...")
        
        return articles
        
    except Exception as e:
        print(f"❌ Chyba při scrapování: {e}")
        return []

# Spuštění příkladu pokud je soubor spuštěn přímo (zůstává stejný)
if __name__ == '__main__':
    # Spustíme příklad použití
    results = asyncio.run(example_usage())
    print(f"\n🎯 Celkem scrapnuto: {len(results)} článků")