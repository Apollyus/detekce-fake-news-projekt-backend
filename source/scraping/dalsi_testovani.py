# Import the summarizer
from summarizer import get_summary

# Your text to summarize
article_text = '''
    Při srážce dvou osobních automobilů došlo ke třem zraněním neslučitelným se životem,“ popsal mluvčí karlovarské krajské záchranky Radek Hes.

Podle informací Novinek měli v jednom z aut jet tři lidé a v druhém pouze osmnáctiletý řidič. Nehodu jako jediná přežila sedmačtyřicetiletá řidička z vozidla s tříčlennou posádkou. Byla transportována vrtulníkem do plzeňské nemocnice.

Žena utrpěla podle dobře informovaného zdroje vážná a mnohačetná poranění, včetně obou dolních i horních končetin, hrudníku, hlavy a také čelisti.

Vozidlo, které řídil osmnáctiletý řidič.

„K nehodě mělo dojít tak, že mladý řidič osobního vozidla značky Volkswagen z dosud nezjištěných příčin přejel do protisměru, kde došlo ke střetu s protijedoucím vozidlem značky Ford,“ upřesnil příčiny nehody mluvčí karlovarské krajské policie Jan Bílek.

„Při dopravní nehodě utrpěl osmnáctiletý řidič zranění neslučitelná se životem, kterým na místě bohužel podlehl,“ pokračoval policejní mluvčí.

„Pětačtyřicetiletý spolujezdec a jednačtyřicetiletá spolujezdkyně z osobního vozidla značky Ford taktéž utrpěli zranění neslučitelná se životem, kterým na místě bohužel podlehli,“ dodal Hes. „Přesná příčina a okolnosti této tragické dopravní nehody jsou nadále v šetření kriminalistů,“ doplnil.

Podle mluvčího karlovarských krajských hasičů Patrika Žižky zůstalo vozidlo Ford s tříčlennou posádkou po nehodě na vozovce, zatímco Volkswagen s mladým řidičem skončilo na střeše mezi vozovkou a objektem bývalé porcelánky. Kvůli vyšetřování příčin nehody byla silnice mezi Loktem a Horním Slavkovem uzavřena. V současné době je již průjezdná se sníženou rychlostí.
'''

# Get a summary with 3 sentences
summary = get_summary(article_text, sentence_count=3)
print(summary)