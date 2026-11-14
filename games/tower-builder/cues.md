# Tower Builder: cues (voice, visuals, teaching) — master doc

Owner decisions of 14 Nov 2026, from the chat that planned flavour and teaching voice-over. This replaces the earlier handoff "Tower Builder: voice lines and sound hooks". Sections 2-6 are BUILT with text boxes (14 Nov; BUILD.md update 39), except the Ur wrong-way demo (open).

The child plays without reading. The game talks to them, shows them what to do with a see-through hand, and makes things glow. The first site teaches everything step by step. Each later site shows its new way of building in a short demo. After that the child plays alone, and the game only adds flavour: stories, facts and the odd remark.

## 1. Words

- **Cue**: something happens in the game, and the game answers with a voice line, a visual sign, a pause, or a mix.
- **Teaching cue**: explains a rule or a control. Always plays, waiting its turn if needed.
- **Flavour cue**: story, praise, facts, remarks.

## 2. Kinds of cue (by how often)

- **First time**, with a scope: ever (saved), per site (saved), or per visit to a site.
- **Every time** it happens.
- **Periodic**: every so many seconds (idle, damaged site).
- **Picking from a group** (idle lines, new-site lines, a site's facts, ...): random, but never one of the last n played, where n = (lines in the group) / 2, rounded down. A group of 1 repeats; a group of 2 alternates; a site's 3 facts never repeat the last one. This replaces "in turn" for the facts.

## 3. Playback rules

- One voice channel. Two voice lines never overlap.
- Three kinds:
  - **Teaching**: always plays; waits its turn.
  - **Queued flavour**: waits its turn and plays in order: intros, win lines, map-after-win lines, new-site and all-finished lines, fail lines, the leave-mid-test line, the test-start line, the welcome lines, the site facts.
  - **Background flavour**: plays only if no voice line is playing or queued, otherwise skipped: idle (81–90), damaged-site reminder (39, after the first time), crumble (72) and snap (73) after the first time.
- When a teaching cue and a flavour cue fire for the same moment, the teaching cue plays and the flavour cue is skipped.
- No voice line starts while a test runs, except: the fail line (74–76, right after the `fail` sound), and the teaching pauses at the start of the wind, load and earthquake, the first time ever.
- The win line plays after the `cheer` sound.
- The parent override (Ctrl) has no voice line.
- Wooden supports and forms are taken out by hand (dragged out, or three quick taps send them back to the pile). The test no longer takes them out; one left in shows red and the building is not ready.

## 4. Visual tools

- **Glow**: the thing talked about pulses (a pile piece, a button, the shovel, a place in the plan, a site on the map).
- **Ghost hand**: a see-through hand acts the action out (drag a piece, tap three times, press a button, pull a form out).
- **Dimming**: the rest of the screen darkens; only the target stays bright.
- **Pause**: the building freezes while the line plays. Used only when the scene would change meanwhile: the start of each test part the first time, the first crumble, the first snap. Tapping anywhere ends the pause.
- **Waits**: a step marked "waits" ends only when the child does the action. Until then the ghost hand repeats it every 8 s (value to tune), without voice.
- **Demo**: on the first visit to a site with something new, after its intro: see-through pieces, carried by the ghost hand at normal speed (like the quick build, not fast), build only the part that shows the new thing, in its real place in the plan, with the lines spoken at their steps. Where a failure is shown, the wrong way is built first and fails (crumbles or falls), then the right way. The see-through pieces then fade; the child's pile is untouched.
- **BUILT (14 Nov)**: the test button is red until the building is ready, then green, with a plain "go" triangle; open sites on the map are yellow (red now only means a damaged site).

## 5. Memory and restart

All memory of cues is one saved record: every first-time mark (ever and per site), each group's recent-lines list, which demos have played. The restart button clears all of it, so after a restart the whole teaching sequence, the demos and the first welcome line (11) play again.

## 6. The teaching sequence

### Map, first launch ever
1. Line 11 (welcome).
2. The only open site glows; the ghost hand taps it. Waits. Line 92.

Every time a locked site is tapped: line 13, and the site to build next glows.

### First site (Mastaba), first visit ever, after intro 1
All steps wait for the child.
1. The ghost hand drags a piece from the pile into the plan. Line 93.
2. The ghost finger taps that piece three times. Line 94.
3. Step 1 again (line 93), so there is something to clear.
4. The shovel glows; the ghost hand taps it. Line 95. Once pressed: line 96.
5. Demo (staggered rows), line 97. Then line 98.
6. After two pieces are in the plan: the red button glows; the ghost hand taps it. Pressing it plays line 70 and shows the red marks. Then line 99.
7. The child builds alone.
8. The button turns green, glows, the ghost hand taps it. Line 100.
9. The test pauses at the start of each part: line 101 (wind), 102 (load), 103 (earthquake).
10. Win: after line 14, line 104. First fail in each part (first time ever per part): the fail line (74/75/76) with the red place glowing, then line 105.
11. After the first win: the map button glows; the ghost hand taps it. Waits. Line 106.
12. On the map, the new yellow site glows and the ghost hand taps it while lines 24 and 34–37 play.

### Whenever it first happens, at any site (first time ever)
- Pickup of each material: lines 78 (mudbrick), 79 (stone), 80 (wood). The Mastaba pile already has wood (its wrong choice), so 80 can first play there.
- First crumble (72) and first snap (73): queued teaching, with a pause and the broken piece glowing. Afterwards background flavour, at most once per visit.
- The pile is empty and the button is still red: the shovel glows. Line 107.
- A new piece shape in the pile: it glows once, no voice.
- A plan has places marked for wood that stays in the building (wood rows, as at Ur and Pharos): they glow. Line 108. Never for wooden supports or forms; those are taught only by the demos and the Ishtar prompt.
- A plan has an opening (door, arch, space between columns): it glows. Line 109.
- A damaged site (red rings) on the map: line 39 queued, the rings glow, the ghost hand taps the site. Afterwards line 39 is background flavour every 60 s while the site is damaged.

### Demos, per site (first visit, after the intro)
What is new comes from the level spec (`levels.md`), level by level.

| Site | New | Demo |
|---|---|---|
| 1 Mastaba | mudbrick; rows with staggered joints | in the teaching sequence, step 5: two mudbricks side by side, one on top across the middle. Line 97 |
| 2 Djoser | stone; heavy low, light high | wrong: a row of mudbrick with more on top; the bottom crumbles. Line 110. Right: a row of stone, mudbrick on top. Line 111 |
| 3 Ur | wood as a row; the long plank spreads the weight | wrong: two short beams under the top terrace; the bricks below crumble. Line 112. Right: the long plank across three mudbricks, two on top over the middle. Line 113 |
| 4 Lion Gate | standing stones and a stone across; a pole held between stones | no demo |
| 5 Karnak | columns, capitals of two small blocks, beams across | a column with two small blocks on it, a second the same, a beam across. Line 114 |
| 6 Ishtar | wedges; the wooden form, taken out after the last wedge | the form on its four blocks (115); wedges from both sides (116); the top wedge (117); the ghost hand pulls the form out, the arch stands (118) |
| 7 Parthenon | drums stacked straight; pediment stones | no demo |
| 8 Mausoleum | wooden posts as temporary props | wrong: the post pulled out before the roof is on; the beam falls. Line 120. Right: post, beam from the core onto it, the roof steps, then the post pulled out. Line 121 |
| 9 Pharos | hollow tower, two walls tied by wooden beams | no demo; the technique is in intro 9 |
| 10 Valens | reusing the forms | no demo; intro 10 says it. A reminder visual: the Ishtar arch demo, then the ghost finger taps the form three times and it goes back to the pile. Line 122 |

**Ishtar, during play** (first time ever): when everything is ready except the form still standing, the form glows and the ghost hand pulls it out. Waits. Line 119. The Mausoleum and Valens are then done alone.

After Valens there is nothing new left to teach.

## 7. All voice lines

Files: `sounds/voice/NN.mp3`, NN = the line number. The owner records in numbered order.

### Existing lines (01–91)

#### Level intros: entering a site that is not finished yet (queued flavour, every time)
1. Mastaba: "Καλώς ήρθες, αρχιτέκτονα, στην Αίγυπτο, γύρω στο 3000 π.Χ. Ως τώρα οι νεκροί θάβονταν σε λάκκους στην άμμο. Οι νέοι άρχοντες όμως θέλουν τάφους αντάξιούς τους: μαστάμπες, πλατιούς τάφους σαν πάγκους. Για πρώτη φορά θα χτίσεις με πλίνθους, τούβλα από λάσπη του Νείλου στεγνωμένα στον ήλιο. Η ιστορία σου αρχίζει εδώ. Χτίσε το!"
2. Djoser: "Καλώς ήρθες ξανά, αρχιτέκτονα, στη Σακκάρα, το ιερό νεκροταφείο της Μέμφιδας, γύρω στο 2650 π.Χ. Οι μαστάμπες σου στέκονται περήφανες, μα ο φαραώ Ζοζέρ θέλει τάφο που να αγγίζει τον ουρανό. Οραματίζεται μαστάμπες τη μία πάνω στην άλλη, ως τους θεούς. Οι πλίνθοι όμως δεν αντέχουν τόσο βάρος. Για πρώτη φορά θα χτίσεις και με πέτρα, η οποία αντέχει πολύ βάρος πάνω της. Εμπρός!"
3. Ur: "Καλώς ήρθες, αρχιτέκτονα, στην πόλη Ουρ. Είμαστε γύρω στο 2100 π.Χ., στη Μεσοποταμία, τη χώρα ανάμεσα στον Τίγρη και τον Ευφράτη. Όπως ο Ζοζέρ, κι ο βασιλιάς Ουρ-Νάμμου θέλει κάτι θεόρατο. Το δικό του όμως δεν είναι τάφος. Είναι σκάλα για τους θεούς, με ναό στην κορυφή για τον Νάννα, τον θεό της Σελήνης. Η πέτρα εδώ σπανίζει, γι' αυτό κράτησέ τη για τη βάση. Από πάνω θα βάλεις πλίνθους, και για πρώτη φορά θα στρώσεις ανάμεσά τους ξύλινες σανίδες. Η σανίδα απλώνει το βάρος σε πολλές πλίνθους από κάτω, κι έτσι δεν θρυμματίζονται. Χτίσε το!" (CHANGED 14 Nov: the wood spreads the weight)
4. Lion Gate: "Καλώς ήρθες, αρχιτέκτονα, στις Μυκήνες, γύρω στο 1250 π.Χ., στην εποχή των ηρώων που θα τραγουδήσει ο Όμηρος. Στην Ουρ η πέτρα ήταν σπάνια. Εδώ, στα βουνά της Ελλάδας, υπάρχει παντού. Ο βασιλιάς Αγαμέμνονας ζώνει την ακρόπολη με τείχη τόσο γιγάντια, που θα λένε πως τα σήκωσαν οι Κύκλωπες. Για πρώτη φορά θα απλώσεις ένα πέτρινο ανώφλι πάνω σε δύο όρθιους λίθους. Από πάνω θα βάλεις το τρίγωνο με τα δύο λιοντάρια. Χτίσε το!"
5. Karnak: "Καλώς ήρθες ξανά στην Αίγυπτο, αρχιτέκτονα, στη Θήβα, γύρω στο 1290 π.Χ. Την ίδια εποχή που οι Μυκηναίοι υψώνουν την πύλη τους, εδώ βασιλεύει ο φαραώ Σέτι ο Πρώτος, κι ύστερα ο γιος του, ο Ραμσής ο Μέγας. Θέλουν για τον θεό Άμμωνα ένα κτίριο με πολλούς κίονες, ένα πέτρινο δάσος. Στις Μυκήνες δύο λίθοι κράτησαν ένα ανώφλι. Εδώ θα στήσεις κίονες και θα απλώσεις από τον έναν στον άλλον πέτρινα δοκάρια. Χτίσε το!"
6. Ishtar (CHANGED 14 Nov: αψίδα → καμάρα): "Καλώς ήρθες, αρχιτέκτονα, στη Βαβυλώνα, γύρω στο 575 π.Χ., μια από τις λαμπρότερες πόλεις του κόσμου, στις όχθες του Ευφράτη. Ο βασιλιάς Ναβουχοδονόσορ θέλει μια πύλη για την Ιστάρ, τη θεά της πόλης. Τα δοκάρια του Καρνάκ όμως γεφυρώνουν μόνο μικρά ανοίγματα. Για μια μεγάλη πύλη χρειάζεσαι κάτι καινούργιο. Για πρώτη φορά θα χτίσεις καμάρα, πάνω σε ξύλινο καλούπι που θα βγάλεις μόλις σταθεί. Μετά από σένα, οι τεχνίτες θα τη ντύσουν με γαλάζια γυαλιστερά τούβλα, με δράκους και ταύρους. Χτίσε το!"
7. Parthenon: "Καλώς ήρθες στην Αθήνα, αρχιτέκτονα, το 447 π.Χ. Οι Πέρσες, που κυρίευσαν τη Βαβυλώνα, έφτασαν ως εδώ και έκαψαν τους ναούς της Ακρόπολης. Νικήθηκαν όμως, κι η Αθήνα ζει τώρα τον χρυσό της αιώνα. Ο Περικλής θέλει στη θέση τους τον ωραιότερο ναό του κόσμου, για τη θεά Αθηνά. Τον σχεδιάζουν ο Ικτίνος και ο Καλλικράτης, με μάρμαρο της Πεντέλης. Για πρώτη φορά θα υψώσεις κίονες σπόνδυλο τον σπόνδυλο, με κιονόκρανα και αέτωμα. Χτίσε το!"
8. Mausoleum: "Καλώς ήρθες, αρχιτέκτονα, στην Αλικαρνασσό, στην απέναντι ακτή του Αιγαίου, γύρω στο 350 π.Χ. Εδώ κυβερνά ο Μαύσωλος. Δεν είναι Έλληνας, μα αγαπά ό,τι είναι ελληνικό. Για τον τάφο του φέρνει τους καλύτερους Έλληνες γλύπτες. Ελληνικοί κίονες σαν του Παρθενώνα θα σηκώσουν μια πυραμίδα με σκαλιά. Από το όνομά του, κάθε μεγάλος τάφος θα λέγεται μαυσωλείο. Για πρώτη φορά θα απλώσεις δοκάρια στον αέρα, πάνω σε ξύλινους στύλους, ώσπου να τα πατήσει η στέγη. Χτίσε το!"
9. Pharos: "Καλώς ήρθες, αρχιτέκτονα, στην Αλεξάνδρεια, γύρω στο 280 π.Χ. Ο Μέγας Αλέξανδρος νίκησε τους Πέρσες και ίδρυσε στην Αίγυπτο αυτή την πόλη με το όνομά του. Όταν πέθανε, ο στρατηγός του, ο Πτολεμαίος, έγινε βασιλιάς της Αιγύπτου. Τώρα οι Πτολεμαίοι θέλουν στο νησάκι Φάρος έναν πύργο τόσο ψηλό, που η φωτιά του θα οδηγεί τα καράβια μέσα στη νύχτα. Από αυτό το νησί κάθε φάρος θα πάρει το όνομά του. Για πρώτη φορά θα χτίσεις ψηλά και κούφια, με δύο τοίχους δεμένους με ξύλινα δοκάρια. Χτίσε το!" (Its technique, two walls tied by wooden beams, is already in it; no demo.)
10. Valens (CHANGED 14 Nov: one form, reused): "Καλώς ήρθες, αρχιτέκτονα, στην Κωνσταντινούπολη, τη νέα πρωτεύουσα της Ρωμαϊκής Αυτοκρατορίας. Ο Μέγας Κωνσταντίνος την ίδρυσε, εδώ στον Βόσπορο. Η καινούργια πόλη όμως διψά, κι ο αυτοκράτορας Ουάλης θέλει να της φέρει νερό πάνω από την κοιλάδα. Οι Ρωμαίοι είναι μάστορες της καμάρας που γνώρισες στη Βαβυλώνα. Τώρα θα στήσεις δύο σειρές από καμάρες, τη μία πάνω στην άλλη. Έχεις όμως μόνο ένα καλούπι για τις καμάρες. Γι' αυτό, από κάθε καμάρα που τελειώνεις, βγάλε το καλούπι για να το ξαναχρησιμοποιήσεις. Εμπρός! Υδροδότησε την πόλη!"

#### Main screen
11. First visit ever (no saved progress), queued: "Καλώς ήρθες στον αρχαίο κόσμο, αρχιτέκτονα! Φαραώ, βασιλιάδες και αυτοκράτορες περιμένουν να τους χτίσεις θαύματα. Πάμε!"
12. Return visit (saved progress), queued: "Καλώς ήρθες ξανά, αρχιτέκτονα! Τα έργα σου σε περιμένουν."
13. Tapping a locked site, teaching, every time (the next site glows): "Αυτός ο τόπος σε περιμένει. Πρώτα χτίσε τον προηγούμενο!"

#### Level won: after the `cheer` sound (queued flavour, every time)
14. Mastaba: "Ο άρχοντας θα αναπαυθεί σε τάφο αντάξιό του. Μπράβο, αρχιτέκτονα!"
15. Djoser: "Ο Ζοζέρ θα ανεβαίνει στον ουρανό από τα σκαλιά σου!"
16. Ur: "Ο Νάννα θα κατεβαίνει από τη Σελήνη στη σκάλα σου!"
17. Lion Gate: "Τα λιοντάρια φυλάνε πια τις Μυκήνες. Μπράβο, αρχιτέκτονα!"
18. Karnak: "Το πέτρινο δάσος του Άμμωνα στέκει περήφανο!"
19. Ishtar: "Η Ιστάρ έχει την πύλη της, κι η Βαβυλώνα λάμπει!"
20. Parthenon: "Η Αθηνά έχει τον ωραιότερο ναό του κόσμου. Μπράβο, αρχιτέκτονα!"
21. Mausoleum: "Το όνομα του Μαύσωλου θα ζει για πάντα!"
22. Pharos: "Η φωτιά του Φάρου θα οδηγεί τα καράβια μέσα στη νύχτα!"
23. Valens: "Το νερό τρέχει στην Κωνσταντινούπολη! Η πόλη δεν διψά πια."

#### First return to the map after a win (queued flavour, once per site)
24. Mastaba: "Η μαστάμπα σου στέκει δίπλα στον Νείλο. Ο πρώτος σου τάφος!"
25. Djoser: "Η πυραμίδα σου υψώνεται πάνω από τη Σακκάρα. Τη βλέπουν από μακριά."
26. Ur: "Στην κορυφή της ζιγκουράτ σου οι ιερείς ανάβουν φωτιές για τον Νάννα."
27. Lion Gate: "Οι πολεμιστές των Μυκηνών περνούν περήφανοι κάτω από την πύλη σου."
28. Karnak: "Οι ιερείς περπατούν στη σκιά του πέτρινου δάσους σου."
29. Ishtar: "Οι πομπές της Βαβυλώνας περνούν κάτω από τη γαλάζια καμάρα σου."
30. Parthenon: "Ο ναός σου λάμπει πάνω στην Ακρόπολη. Όλη η Αθήνα τον κοιτάζει."
31. Mausoleum: "Το μαυσωλείο σου φαίνεται από τη θάλασσα. Οι ναύτες το δείχνουν ο ένας στον άλλον."
32. Pharos: "Απόψε η φωτιά του Φάρου σου θα φέρει τα καράβια σπίτι τους."
33. Valens: "Το νερό κυλά πάνω από τις καμάρες σου. Η πόλη ξεδιψά."

#### Right after 24–33, if that win opened a new site (group; queued flavour; the new site glows the first time ever)
34. "Ένας νέος βασιλιάς σε καλεί!"
35. "Η φήμη σου ταξίδεψε μακριά. Σε ζητούν σε νέο τόπο!"
36. "Κάποιος ψάχνει τον καλύτερο αρχιτέκτονα του κόσμου. Εσένα!"
37. "Ένα καινούργιο έργο σε περιμένει. Δες πού!"

#### Right after 33, when all ten sites are finished (instead of 34–37)
38. "Από τον Νείλο ως τον Βόσπορο, ωραΐσες την οικουμένη με τα έργα σου!"

#### Damaged site (a finished site whose headpiece is out of place)
- On the map, every 60 s, the site flashes with red rings.
39. "Το έργο σου χάλασε! Έλα να το φτιάξεις." First time ever: teaching (queued, rings glow, ghost hand taps the site). Then background flavour with the flashing.

#### Entering a finished site: one fact per visit (group of 3 per site; queued flavour)
40. Mastaba: "Οι άνθρωποι του Νείλου έλεγαν πως ο θάνατος είναι δρόμος προς τη Δύση, εκεί όπου πεθαίνει κάθε βράδυ ο ήλιος. Γι' αυτό έχτιζαν στους νεκρούς τους σπίτια για την αιωνιότητα."
41. Mastaba: "Όταν ο Σείριος ξαναφαινόταν πριν από την αυγή, ο Νείλος φούσκωνε και σκέπαζε τη γη. Κι όταν αποτραβιόταν, άφηνε τη μαύρη λάσπη, το δώρο του, από την οποία πλάστηκαν οι πλίνθοι σου."
42. Mastaba: "Πίστευαν πως όσο λέγεται το όνομα ενός νεκρού, εκείνος δεν χάνεται ολότελα. Κι ίσως είχαν δίκιο, γιατί κάποια ονόματα τα λέμε ακόμα, πέντε χιλιάδες χρόνια μετά."
43. Djoser: "Πριν από τον Ζοζέρ, κανείς δεν είχε υψώσει βουνό από πέτρα κάτω από τον ουρανό. Κι όσοι έχτισαν ύστερα, όλοι πάτησαν στα σκαλιά του."
44. Djoser: "Ο Ιμχοτέπ ήταν χτίστης, γιατρός και σοφός, κι η φήμη του ξεπέρασε τον θάνατο. Αιώνες αργότερα οι άνθρωποι τον προσκυνούσαν σαν θεό."
45. Djoser: "Δεκατέσσερις πύλες είχε το τείχος του, μα μόνο μία άνοιγε για τους ζωντανούς. Από τις άλλες περνούσαν μόνο τα πνεύματα."
46. Ur: "Η γη ανάμεσα στα δύο ποτάμια ήταν επίπεδη ως την άκρη του ουρανού. Γι' αυτό οι Σουμέριοι έχτισαν μόνοι τους ένα βουνό, για να φτάσουν τους θεούς."
47. Ur: "Εδώ οι άνθρωποι έμαθαν, από τους πρώτους στον κόσμο, να γράφουν σε πηλό με την άκρη ενός καλαμιού. Οι πινακίδες κοιμήθηκαν στη γη χιλιάδες χρόνια, ώσπου ξύπνησαν και μίλησαν ξανά."
48. Ur: "Η Ουρ έγινε σκόνη, κι ο Ευφράτης την εγκατέλειψε κι άλλαξε δρόμο. Μα η ζιγκουράτ στέκει ακόμα στην έρημο, και θυμάται."
49. Lion Gate: "Όταν οι Έλληνες των κατοπινών χρόνων είδαν αυτά τα τείχη, δεν πίστεψαν πως τα σήκωσαν άνθρωποι. Είπαν πως τα έχτισαν οι Κύκλωπες, οι μονόφθαλμοι γίγαντες, κι έτσι τα λέμε ως σήμερα κυκλώπεια."
50. Lion Gate: "Από εδώ, λέει ο θρύλος, ξεκίνησε ο βασιλιάς Αγαμέμνονας για την Τροία. Δέκα χρόνια κράτησε ο πόλεμος, κι όταν γύρισε, η πύλη τον περίμενε ακόμα."
51. Lion Gate: "Τα λιοντάρια της πύλης είναι το παλαιότερο μεγάλο γλυπτό της Ευρώπης. Τα κεφάλια τους χάθηκαν μέσα στους αιώνες, μα στέκονται ακόμα στη θέση τους και φυλάνε μια πόλη που δεν υπάρχει πια."
52. Karnak: "Πάνω από δύο χιλιάδες χρόνια έχτιζαν οι φαραώ στο Καρνάκ, κι ο καθένας πρόσθετε κάτι δικό του. Κανείς δεν το τελείωσε, γιατί ένας τέτοιος ναός δεν τελειώνει ποτέ."
53. Karnak: "Οι κίονες έχουν το σχήμα του πάπυρου, του καλαμιού του Νείλου. Οι Αιγύπτιοι πίστευαν πως στην αρχή του κόσμου υπήρχαν μόνο νερά και καλαμιές, κι ο ναός ήταν εκείνος ο πρώτος βάλτος, γινωμένος πέτρα."
54. Karnak: "Κάποτε οι κίονες ήταν βαμμένοι με λαμπερά χρώματα. Ο ήλιος κι οι αιώνες τα έσβησαν ένα ένα, μα οι σκαλισμένες μορφές θυμούνται ακόμα το σχήμα τους."
55. Ishtar: "Γαλάζια σαν τον ουρανό ήταν η πύλη, με ταύρους και δράκους να βαδίζουν πάνω στα γυαλιστερά τούβλα. Όποιος περνούσε από κάτω ήξερε πως έμπαινε σε μια από τις μεγαλύτερες πόλεις του κόσμου."
56. Ishtar: "Λένε πως στη Βαβυλώνα υπήρχαν κήποι κρεμασμένοι στον αέρα, ένα από τα επτά θαύματα του κόσμου. Μα κανείς ως σήμερα δεν βρήκε τα ίχνη τους, κι ίσως κοιμούνται ακόμα κάτω από την άμμο."
57. Ishtar: "Οι σοφοί της Βαβυλώνας κοίταζαν τον ουρανό κάθε νύχτα και κατέγραφαν την πορεία των άστρων. Με τα χρόνια έμαθαν να προλέγουν πότε η Σελήνη θα σκοτεινιάσει."
58. Parthenon: "Λίγες γραμμές στον Παρθενώνα είναι αληθινά ίσιες. Οι χτίστες του ήξεραν πως το μάτι ξεγελιέται, κι έτσι τον λύγισαν απαλά, ώστε να φαίνεται τέλειος σε όποιον τον κοιτάζει."
59. Parthenon: "Μέσα στο μισόφωτο του ναού στεκόταν η Αθηνά του Φειδία, ψηλή σαν δέντρο, ντυμένη χρυσάφι κι ελεφαντόδοντο. Χάθηκε πριν από πολλούς αιώνες, κι από τη λάμψη της έμειναν μόνο ιστορίες."
60. Parthenon: "Στην Αθήνα, για πρώτη φορά, οι πολίτες ψήφιζαν οι ίδιοι για τους νόμους τους. Κι ο ναός της θεάς δεν χτίστηκε με διαταγή βασιλιά, αλλά με απόφαση του λαού."
61. Mausoleum: "Ο Μαύσωλος πέθανε πριν τελειώσει ο τάφος του, κι ύστερα πέθανε κι η Αρτεμισία, η γυναίκα του. Μα οι γλύπτες δεν άφησαν το έργο· έμειναν και το τελείωσαν, για τη δόξα της τέχνης τους."
62. Mausoleum: "Ήταν ένα από τα επτά θαύματα του κόσμου και στάθηκε πάνω από χίλια πεντακόσια χρόνια. Ώσπου ήρθαν οι σεισμοί και το γκρέμισαν."
63. Mausoleum: "Ιππότες από μακρινή χώρα μάζεψαν τις πέτρες του κι έχτισαν ένα κάστρο, που στέκει ως σήμερα. Έτσι οι πέτρες του θαύματος δεν χάθηκαν· απλώς άλλαξαν όνομα."
64. Pharos: "Τη νύχτα, στην κορυφή του πύργου, έκαιγε μια φωτιά που φαινόταν από μακριά στο πέλαγος. Κι οι ναύτες, βλέποντάς την, ήξεραν πως ο δρόμος για το σπίτι ήταν ανοιχτός."
65. Pharos: "Λένε πως ο χτίστης του, ο Σώστρατος, χάραξε το όνομά του στην πέτρα, το σκέπασε με σοβά κι από πάνω έγραψε το όνομα του βασιλιά. Τα χρόνια έφαγαν τον σοβά, κι έμεινε μόνο το όνομα του αρχιτέκτονα."
66. Pharos: "Πάνω από χίλια πεντακόσια χρόνια φύλαγε το λιμάνι, ώσπου οι σεισμοί τον έριξαν στη θάλασσα. Οι πέτρες του κείτονται ακόμα στον βυθό, κι οι δύτες κατεβαίνουν να τις βρουν."
67. Valens: "Από μακρινά βουνά ερχόταν το νερό, μέσα από αυλάκια που έτρεχαν εκατοντάδες χιλιόμετρα. Κι όλο τον δρόμο κατέβαινε τόσο απαλά, που κυλούσε μόνο του, χωρίς καμία μηχανή."
68. Valens: "Αυτοκράτορες ήρθαν κι έφυγαν, κι ύστερα σουλτάνοι, κι η πόλη άλλαξε όνομα. Μα το υδραγωγείο έφερνε νερό σε όλους, για πάνω από χίλια πεντακόσια χρόνια."
69. Valens: "Στέκει ακόμα σήμερα, κι από κάτω του περνούν κάθε μέρα άνθρωποι βιαστικοί. Λίγοι σηκώνουν τα μάτια, μα οι καμάρες περιμένουν, όπως περιμένουν εδώ και χίλια εξακόσια χρόνια."

#### Build screen
70. Red test button pressed while the building is not ready (with the `not-ready` sound and the red marks), teaching, every time: "Λείπουν ακόμα κομμάτια από το σχέδιο."
71. Test starts (green button), queued flavour, every time, before the test runs: "Ας δούμε αν θα αντέξει!"
72. Mudbrick crumbles: first time ever teaching (pause, glow); then background, at most once per visit: "Η λάσπη θρυμματίστηκε κάτω από το βάρος."
73. Wood snaps: first time ever teaching (pause, glow); then background, at most once per visit: "Το ξύλο έσπασε πάνω από το κενό."
74. Test fails in the wind: "Ο άνεμος το γκρέμισε. Ξαναδοκίμασε!"
75. Test fails in the load: "Δεν άντεξε το βάρος. Ξαναδοκίμασε!"
76. Test fails in the earthquake: "Ο σεισμός το γκρέμισε. Ξαναδοκίμασε!"
   (74–76: first fail ever in each part is teaching, the red place glows, then line 105; afterwards queued flavour.)
77. Leaving the site mid-test without a pass, queued flavour: "Πού πας, αρχιτέκτονα; Κομμάτια και σπαράγματα θα σε περιμένουν!"
78. First pickup of a mudbrick ever, teaching: "Πλίνθοι από λάσπη: ελαφριοί, μα δεν αντέχουν μεγάλο βάρος." (Checked in the game: mudbrick is lighter than stone and heavier than wood.)
79. First pickup of stone ever, teaching: "Η πέτρα είναι βαριά, μα αιώνια."
80. First pickup of wood ever, teaching: "Το ξύλο γεφυρώνει κενά, μα σπάει αν το φορτώσεις πολύ."

#### Idle: no input for 60 s, on the map or the build screen, not during a test (group; background flavour)
- Line 81 only on the map while visitors are walking to a site.
- Line 86 is the owner's own text; attach the recording to slot 86.
81. "Κοίτα! Άνθρωποι φτάνουν από μακριά να θαυμάσουν τα έργα σου!"
82. "Ένα καλό θεμέλιο δεν το βλέπει κανείς. Χωρίς αυτό όμως, τίποτα δεν στέκει."
83. "Α! Τι ωραία βαρκούλα! Θα 'θελα να 'χα μια βαρκούλα."
84. "Τι ωραία που είναι εδώ…"
85. "Η γνώση… το πιο πολύτιμο στο σύμπαν. Την είδαν λίγοι, κι ελάχιστοι τη μοιράστηκαν."
86. (the owner's own text)
87. "Λοιπόν, εγώ είμαι ο γκρεμιστής, γιατί είμαι εγώ κι ο χτίστης!"
88. "Κοίτα τον ουρανό, αρχιτέκτονα. Όσο ψηλά κι αν χτίσεις, εκείνος θα είναι πάντα λίγο ψηλότερα."
89. "Τα κτίρια ζουν περισσότερο από αυτούς που τα χτίζουν. Τα έργα σου θα τα δουν παιδιά που δεν έχουν γεννηθεί ακόμα."
90. "Ποιο έργο σου θα στέκει σε χίλια χρόνια; Οι καλοί αρχιτέκτονες το σκέφτονται πάντα."

#### Buttons
91. Restart button, first press (a second press erases), teaching, every time: "Αυτό το κουμπί σβήνει όλη σου την πρόοδο, κι αρχίζεις το χτίσιμο από την αρχή. Αν αυτό θέλεις, ξαναπάτα το."

### New teaching lines (92–122)
92. Map, first launch, tap the open site: "Πάτα εδώ για να ξεκινήσεις!"
93. Drag a piece into the plan: "Πιάσε ένα κομμάτι από εδώ και βάλ' το μέσα στο σχέδιο."
94. Three taps: "Αν πατήσεις ένα κομμάτι τρεις φορές γρήγορα, γυρίζει πίσω στον σωρό. Δοκίμασε!"
95. Shovel: "Πάτα το φτυάρι!"
96. After the shovel: "Το φτυάρι μαζεύει όλα τα κομμάτια και τα γυρίζει στον σωρό. Έτσι ξαναρχίζεις από την αρχή."
97. Mastaba demo: "Βάλε κάθε τούβλο πάνω σε δύο από κάτω, όχι πάνω σε ένα. Έτσι ο τοίχος δένει."
98. "Τώρα χτίσε! Γέμισε όλο το σχέδιο."
99. Red button: "Αυτό είναι το κουμπί της δοκιμής. Όσο είναι κόκκινο, το κτίριο δεν είναι έτοιμο. Όταν γεμίσεις το σχέδιο, θα γίνει πράσινο."
100. Green button: "Το κουμπί πρασίνισε! Πάτα το να δεις αν το κτίριο αντέχει."
101. Wind: "Πρώτα έρχεται ο άνεμος. Θα σπρώξει το κτίριο από τη μια μεριά κι από την άλλη."
102. Load: "Τώρα θα κατέβει ένα βάρος πάνω στο κτίριο. Θα το αντέξει;"
103. Earthquake: "Και τώρα σεισμός! Η γη θα τρέμει."
104. First win: "Άντεξε τον άνεμο, το βάρος και τον σεισμό. Το έργο σου στέκει!"
105. First fail in a part: "Το κόκκινο δείχνει πού χάλασε. Φτιάξ' το εκεί και ξαναδοκίμασε!"
106. Map button: "Πάτα εδώ για να γυρίσεις στον χάρτη."
107. Pile empty: "Τελείωσαν τα κομμάτια. Με το φτυάρι τα μαζεύεις όλα και ξαναρχίζεις."
108. Wood places: "Σε αυτά τα σημεία μπαίνει ξύλο."
109. Openings: "Αυτό το άνοιγμα μένει άδειο. Μην το κλείσεις!"
110. Djoser demo, wrong: "Αν βάλεις πλίνθους κάτω, θρυμματίζονται κάτω από το βάρος."
111. Djoser demo, right: "Η πέτρα είναι γερή: βάλ' την κάτω, εκεί που πέφτει όλο το βάρος. Οι πλίνθοι πάνε ψηλά."
112. Ur demo, wrong: "Με δύο κοντά δοκάρια, όλο το βάρος πέφτει στη μέση, και τα τούβλα θρυμματίζονται."
113. Ur demo, right: "Η μακριά σανίδα απλώνει το βάρος σε όλα τα τούβλα από κάτω, κι έτσι αντέχουν."
114. Karnak demo: "Πάνω σε κάθε κίονα βάζεις δύο μικρές πέτρες. Το δοκάρι πατάει με κάθε άκρη του πάνω τους."
115. Ishtar demo: "Πρώτα στήνεις το ξύλινο καλούπι."
116. Ishtar demo: "Πάνω του βάζεις τις σφήνες, από τις δύο μεριές."
117. Ishtar demo: "Η τελευταία σφήνα μπαίνει στην κορυφή και κλειδώνει την καμάρα."
118. Ishtar demo: "Τώρα βγάζεις το καλούπι. Η καμάρα στέκει μόνη της!"
119. Ishtar, during play: "Η καμάρα στέκει. Τώρα βγάλε το ξύλινο καλούπι!"
120. Mausoleum demo, wrong: "Αν βγάλεις τον στύλο πριν πατήσει η στέγη, το δοκάρι πέφτει."
121. Mausoleum demo, right: "Στήριξε πρώτα το δοκάρι σε έναν ξύλινο στύλο. Όταν πατήσει η στέγη από πάνω, βγάζεις τον στύλο."
122. Valens reminder: "Με τρία γρήγορα πατήματα, το καλούπι γυρίζει στον σωρό, έτοιμο για την επόμενη καμάρα."

## 8. Notes

- Mausoleum (owner, 14 Nov): the posts stay; when he builds, the beams fall without them. The demo shows that failure.
- Valens (owner, 14 Nov): the level now has one form on one block; the quick build makes the arches one after another, taking the form out of each. Built and pushed.
- Lines 03, 06 and 10 changed (wood spreads the weight; καμάρα; one form). If they were already recorded, they need recording again.

## 9. Build now: text instead of voice (owner, 14 Nov)

Until the recordings exist, every voice line is shown as its Greek text on a white box. The recordings replace the box later through the same hook (line number = file number).

- One model: a line "plays" while its box is up. The box lasts 2 s, with a blue bar on top running out, then closes by itself (owner, 14 Nov); ESC closes it early. So everything in section 3 holds as written: one line at a time, the queue waits for ESC, background lines are skipped while a box is up.
- Blocking boxes freeze the game (physics, test, input) until ESC, as the paused voice line would: the pauses (start of wind, load and earthquake the first time; first crumble; first snap) and every line of a demo (the demo goes on to its next step after ESC).
- All other boxes do not block: the child can keep playing while the box is up. Teaching steps that wait for an action end when the action is done, and their box goes with them.
- When `sounds/voice/NN.mp3` exists, it plays instead of the box, and ends on its own.

## 10. Where the hooks go in the code (`src/index.html`)

Map the code with `grep -n "SECTION:"` first. Hook points, by what the child does:

- Sounds: `playSound` and the `SOUNDS` table (FEEL section). Voice is a separate single channel next to it.
- Saved progress: `progress`, saved with `SAVE_KEY` (LEVELS section). Cue memory goes in the same saved record, so `restartAll()` (MAP section), which removes it, clears the cues too.
- Map: tapping a site, locked or open; the red-ring flashing of a damaged site uses `headpieceOut()` / `syncSite()`; the visitors' tour and the boats are in the MAP section.
- Entering a site: `startLevel(i)`. Back to the map: `goMap()` (the home button).
- Pointer: buttons in POINTER HANDLING (`home`, `broom` = the shovel, `test`); three taps send a piece back at `piece.taps.length >= 3`; `undo()`.
- Test button: `startTest()`, its not-ready branch (the `not-ready` sound, red marks) and its ready branch; ready state is `readySince`.
- Test parts and result: the phase names in the LEVELS section (supports, settle, wind, load, quake, fail, pass); leaving mid-test is `abortTest()`; a win is `celebrate()`.
- Breaking: `crumble()` and `snapWood()` (BREAKING section).
- The quick build's step list (`solution` in `src/levels.js`, with its `pull` steps) is what the demos replay at normal speed, as see-through pieces, limited to the part each demo shows.
