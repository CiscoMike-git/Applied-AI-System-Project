KNOWLEDGE_BASE: dict[str, str] = {
    "dog_feeding": (
        "Adult dogs generally thrive on two meals per day — morning and evening — spaced roughly "
        "8-12 hours apart. Consistent meal timing supports digestive health and helps prevent "
        "bloat (gastric dilatation-volvulus), which is especially risky in large and deep-chested "
        "breeds. Puppies under six months typically need three to four smaller meals daily. "
        "Free-feeding (leaving food out all day) can lead to obesity and makes it harder to notice "
        "changes in appetite that signal illness. Portion size should be based on the dog's ideal "
        "body weight, not current weight, and adjusted for activity level and life stage. "
        "Fresh water should always be available. Avoid feeding immediately before or after "
        "vigorous exercise; a 30-60 minute buffer reduces bloat risk. High-quality protein should "
        "be the first ingredient. Treats should make up no more than 10% of daily calories."
    ),
    "dog_exercise": (
        "Most adult dogs need 30-60 minutes of moderate exercise per day, though high-energy "
        "breeds like Border Collies and Huskies may need 1-2 hours. Exercise needs decline "
        "somewhat in senior dogs but should not be eliminated — shorter, gentler walks help "
        "maintain joint mobility and mental engagement. Morning walks are beneficial because "
        "they establish a bathroom routine, burn off overnight energy, and set a calm tone for "
        "the day. Evening walks help dogs decompress and can improve nighttime sleep. Avoid "
        "intense exercise in extreme heat; walk during cooler morning or evening hours and check "
        "pavement temperature with your hand before walking on hot days. Mental stimulation "
        "(puzzle feeders, training, sniff walks) counts as exercise and reduces destructive "
        "behavior. Puppies should follow the '5-minute rule': 5 minutes per month of age twice "
        "daily to avoid stressing developing joints."
    ),
    "dog_grooming": (
        "Brushing frequency depends on coat type: short-haired dogs benefit from weekly brushing "
        "to remove loose fur and distribute skin oils; medium and long-haired dogs typically need "
        "brushing 3-5 times per week to prevent mats. Bathing every 4-6 weeks is sufficient for "
        "most dogs unless they get visibly dirty. Over-bathing strips natural oils. Use a "
        "dog-specific shampoo; human shampoos disrupt the dog's slightly acidic skin pH. "
        "Nails should be trimmed every 3-4 weeks; overgrown nails cause gait problems and joint "
        "stress. If you hear clicking on hard floors, the nails are too long. Ear checks once a "
        "week can catch infections early — healthy ears are pink, odorless, and not itchy. "
        "Dental care is critical: brushing teeth 2-3 times per week (or daily) prevents periodontal "
        "disease, which affects over 80% of dogs by age 3 and can lead to systemic health issues. "
        "Introduce grooming routines early to build positive associations."
    ),
    "dog_health": (
        "Annual veterinary wellness exams are the minimum for adult dogs; senior dogs (7+ years "
        "for most breeds) benefit from twice-yearly checkups. Core vaccines include distemper, "
        "parvovirus, hepatitis (DAP), and rabies — confirm schedules with your vet. Flea, tick, "
        "and heartworm prevention should be administered monthly year-round in most climates. "
        "Spayed or neutered dogs generally have lower rates of certain cancers and behavioral "
        "issues. Monitor for warning signs: changes in appetite or thirst, sudden weight change, "
        "limping, coughing, unusual lumps, changes in bathroom habits, or behavioral shifts. "
        "Dental disease is the most common preventable illness. Keep a health journal noting "
        "any changes. Obesity is the most widespread preventable condition — keep your dog at "
        "a healthy weight with ribs easily palpable but not visible. Have a pet first-aid kit "
        "and know the location of the nearest emergency veterinary clinic."
    ),
    "cat_feeding": (
        "Cats are obligate carnivores with a biological need for animal-based protein and "
        "taurine, which is absent in plant foods. Most adult cats do well with two scheduled "
        "meals per day; free-feeding dry food often leads to obesity because cats lack strong "
        "satiety signals. Wet food (canned or pouched) is highly beneficial as cats have low "
        "thirst drives and naturally obtain most moisture from prey — wet food helps prevent "
        "urinary tract disease and kidney problems, which are common in cats fed solely dry food. "
        "Kittens need more frequent feeding (3-4 times daily) until about 6 months. Senior cats "
        "over 11 years may benefit from more calorie-dense food as they can lose lean muscle. "
        "Avoid sudden food changes; transition over 7-10 days to prevent GI upset. Provide fresh "
        "water daily in a wide, clean bowl — many cats prefer running water (a fountain). "
        "Treats should be limited to avoid caloric imbalance."
    ),
    "cat_exercise": (
        "Indoor cats need active encouragement to exercise because their environment lacks the "
        "natural stimulation of hunting. Aim for at least 2-3 play sessions of 10-15 minutes "
        "each day using interactive toys (wand toys, laser pointers) that mimic prey movement. "
        "Play is most effective in the morning and evening when cats are naturally most active. "
        "Environmental enrichment — cat trees, window perches, puzzle feeders, and hiding spots "
        "— reduces boredom and stress. Without adequate exercise, cats are prone to obesity, "
        "diabetes, and behavioral problems like excessive meowing or furniture scratching. "
        "Senior cats play less but still benefit from gentle, shorter sessions. Rotate toys "
        "to maintain novelty. Some cats enjoy harness walks outdoors; introduce the harness "
        "slowly indoors first. Scratching posts provide both physical activity and essential "
        "claw maintenance — place them near sleeping areas where cats naturally stretch."
    ),
    "cat_grooming": (
        "Most short-haired cats are effective self-groomers and need brushing only once or twice "
        "a week to reduce shedding and hairballs. Long-haired breeds (Maine Coon, Persian, "
        "Ragdoll) require daily brushing to prevent painful mats. Use a metal comb or slicker "
        "brush and work gently to build a positive grooming association. Bathing is rarely "
        "necessary for cats; most strongly dislike it and manage well without it. However, cats "
        "with skin conditions or those that get into something sticky may need occasional baths "
        "with a cat-safe shampoo. Nail trimming every 2-3 weeks prevents overgrowth and "
        "reduces scratching damage. Dental care is often overlooked but critical — periodontal "
        "disease is one of the most common feline illnesses. Brushing teeth several times weekly "
        "is ideal; dental treats and water additives are secondary aids. Check ears weekly for "
        "dark debris (a sign of ear mites) or redness. Litter box hygiene directly affects "
        "grooming behavior — a clean box reduces stress and supports normal grooming patterns."
    ),
    "cat_health": (
        "Cats are masters at hiding illness, making annual veterinary exams essential — twice "
        "yearly for cats over 7. Core vaccinations include panleukopenia, herpesvirus-1, "
        "calicivirus (FVRCP), and rabies; your vet will advise on lifestyle-based additions "
        "like FeLV (for outdoor cats). Common preventable conditions include obesity, dental "
        "disease, urinary tract problems, and hyperthyroidism in seniors. Watch for warning "
        "signs: hiding more than usual, changes in litter box habits (straining to urinate is "
        "an emergency in male cats), weight loss despite normal eating, excessive thirst, "
        "vomiting more than once or twice per week, and grooming changes. Cats are sensitive "
        "to many household toxins including lilies (highly toxic — even small exposures can "
        "cause acute kidney failure), certain essential oils, and human pain medications. "
        "Spaying/neutering reduces cancer risk and eliminates heat-cycle stress. Indoor cats "
        "live significantly longer on average than outdoor cats. Microchipping and a collar ID "
        "are recommended even for indoor cats."
    ),
    "general_scheduling": (
        "When scheduling multiple pets, batch tasks by pet rather than interleaving them to "
        "reduce owner context-switching and transition time. For example, complete all tasks "
        "for Pet A before moving to Pet B. When two pets have competing high-priority tasks at "
        "the same time (e.g., both need morning feeding), prioritize the pet with the more "
        "time-sensitive need — a diabetic cat needing insulin with food takes priority over a "
        "healthy dog that can wait 10 minutes. Build buffer time between tasks (5-10 minutes) "
        "when possible to accommodate the unpredictability of pet care — a dog walk that "
        "encounters another dog, or a cat that resists medication. Morning routines set the "
        "tone for the day; prioritize high-stakes tasks (medication, feeding) in the morning "
        "window when energy and focus are highest. Avoid scheduling grooming or stress-inducing "
        "tasks immediately before or after high-energy exercise, as the pet will be too "
        "stimulated or tired to cooperate. Use consistent daily timing for recurring tasks like "
        "feeding and walks — pets adapt their biological rhythms to predictable schedules, "
        "which reduces anxiety and improves cooperation."
    ),
    "task_prioritization": (
        "When available time is limited, prioritize tasks using this hierarchy: (1) Medical and "
        "health-critical tasks — medication administration, insulin injections, wound care, or "
        "any task prescribed by a vet. Missing these can have serious consequences. (2) Feeding "
        "— hunger affects behavior and skipping meals disrupts digestion and metabolic rhythms. "
        "(3) Elimination-related tasks — outdoor walks for dogs, litter box cleaning for cats. "
        "Holding urine too long increases UTI risk; a dirty litter box causes stress and avoidance. "
        "(4) Exercise — important for physical and mental health but a single missed session has "
        "low immediate harm. (5) Social interaction and enrichment — play, training, and bonding "
        "time. (6) Grooming — unless the animal is in visible discomfort (matted coat, overgrown "
        "nails), a single missed grooming session is low-risk. Low-priority tasks that have been "
        "skipped multiple times accumulate urgency — a long-skipped nail trim eventually becomes "
        "high priority. When prioritizing across multiple pets, give weight to animals with "
        "health conditions, age-related needs, or behavioral issues that worsen without routine."
    ),
    "rabbit_feeding": (
        "Rabbits require unlimited fresh grass hay (timothy, orchard grass, or meadow hay) as "
        "80% or more of their diet — hay is critical for dental wear and gut motility. Leafy "
        "greens (romaine, cilantro, parsley, basil, arugula) should be offered daily at roughly "
        "1 cup per 2 pounds of body weight. Pellets should be limited to 1/8–1/4 cup per 5 "
        "pounds of body weight daily; excessive pellets lead to obesity and suppress hay "
        "consumption. Fresh water must always be available. Avoid sugary fruits, starchy "
        "vegetables (corn, peas, beans), and grains. Introduce new foods gradually over 1–2 "
        "weeks to avoid GI upset. Young rabbits under 6 months should eat unlimited pellets "
        "with unlimited hay; the diet shifts to hay-focused after 6 months."
    ),
    "rabbit_exercise": (
        "Rabbits need at least 3–4 hours of free-roaming exercise daily in a rabbit-proofed "
        "space — cords, toxic houseplants, and baseboards must be secured. Confinement without "
        "exercise causes muscle atrophy, obesity, and behavioral problems like destructive "
        "chewing and aggression. Rabbits express happiness through 'binkying' — twisting jumps "
        "that require enough open space to perform. Exercise is best offered in the morning and "
        "evening when rabbits are naturally most active (they are crepuscular). An enclosure of "
        "at least 4× the rabbit's body length in each dimension is the minimum acceptable size; "
        "larger is always better. Outdoor time in an enclosed pen can provide additional "
        "enrichment but requires supervision for predators and toxic plants."
    ),
    "rabbit_grooming": (
        "Short-haired rabbits need brushing 1–2 times per week; during heavy shedding seasons "
        "(spring and fall), daily brushing prevents accidental fur ingestion — unlike cats, "
        "rabbits cannot vomit, putting them at risk for fatal GI blockages from fur. Long-haired "
        "breeds (Angora, Jersey Wooly) require daily combing to prevent painful mats. Never "
        "bathe a rabbit — they are highly prone to hypothermia and shock from bathing; "
        "spot-clean soiled areas with a damp cloth instead. Nails should be trimmed every "
        "6–8 weeks; overgrown nails can catch on surfaces and tear. Check the dewlap (fold "
        "under the chin in females) for moisture or sores. Scent glands on either side of the "
        "genitals require occasional gentle cleaning with a cotton swab."
    ),
    "rabbit_health": (
        "Rabbits mask illness until critically ill, making twice-yearly veterinary exams "
        "strongly recommended. Spaying females is especially important: unspayed females have "
        "an approximately 80% chance of uterine cancer by age 5. GI stasis — when gut motility "
        "slows or stops — is a life-threatening emergency; signs include not eating, no fecal "
        "pellets for 12+ hours, hunched posture, and tooth grinding. Always have an emergency "
        "rabbit-savvy vet identified in advance. Dental disease is extremely common because "
        "rabbit teeth grow continuously — misalignment leads to spurs that cut the tongue and "
        "cheeks; symptoms include drooling, dropping food, and weight loss. E. cuniculi (a "
        "parasitic infection) can cause sudden head tilt or neurological symptoms. Keep the "
        "environment below 80°F/27°C — rabbits are highly susceptible to heat stroke."
    ),
    "bird_feeding": (
        "Seed-only diets are nutritionally deficient and a leading cause of disease in pet "
        "birds. A balanced diet should consist of 60–80% high-quality species-appropriate "
        "pellets (Harrison's, Zupreem, Roudybush) supplemented with fresh vegetables (dark "
        "leafy greens, bell peppers, carrots), small amounts of fruit, and limited seeds or "
        "nuts as treats. Foods toxic to birds include avocado, chocolate, caffeine, alcohol, "
        "onions, garlic, and fruit pits or seeds. Fresh water must be changed daily — bacteria "
        "grow quickly in water dishes. Grit is not needed by most companion birds (parrots, "
        "budgies, cockatiels) since they hull their seeds. Cooking sprays and non-stick pans "
        "(PTFE/Teflon) release fumes that can be lethal to birds — use only bird-safe cookware."
    ),
    "bird_exercise": (
        "Birds need a minimum of 2–4 hours outside their cage daily in a safe, supervised "
        "environment to maintain physical health and mental wellbeing. Without enrichment and "
        "out-of-cage time, birds develop feather-destructive behaviors (over-preening, "
        "plucking), screaming, biting, and depression. Interactive play with foraging toys — "
        "paper, puzzle boxes, shreddable materials — satisfies natural foraging instincts; "
        "birds in the wild spend 60–70% of their day foraging. Rotate toys regularly to "
        "maintain novelty. Social interaction is critical for flock species (most parrots, "
        "cockatiels, budgies): a solitary bird requires significantly more owner interaction. "
        "Flight provides the primary cardiovascular exercise for unclipped birds; ensure "
        "windows and mirrors are clearly marked to prevent dangerous collisions."
    ),
    "bird_grooming": (
        "Birds preen constantly to maintain feather alignment and waterproofing; monitor preening "
        "for signs of over-preening or feather-plucking, which signals stress, illness, or "
        "boredom rather than a routine grooming need. Misting with a spray bottle or providing "
        "a shallow dish of water lets birds bathe naturally — most enjoy this 2–3 times per week; "
        "avoid cold water. Wing clipping is optional and debated; if done, it should be performed "
        "by a vet or experienced groomer, leaving enough feathers for a controlled glide. Nails "
        "should be trimmed every 2–3 months or when they become hooked and catch on cage bars; "
        "use bird-specific clippers or have a vet handle it. Beak trimming is almost never needed "
        "in healthy birds with appropriate perches and foraging toys — an overgrown beak usually "
        "signals nutritional deficiency or underlying illness. Cuttlebones and mineral blocks "
        "support beak conditioning. Clean food and water dishes daily; bacteria and mold in dirty "
        "dishes are a leading cause of disease. Rotate cage liners daily and thoroughly clean the "
        "cage weekly with a bird-safe disinfectant."
    ),
    "bird_health": (
        "Birds are prey animals and hide illness until severely compromised — visible symptoms "
        "often mean a veterinary emergency. Establish care with an avian-certified veterinarian "
        "and schedule annual wellness exams including a fecal float for parasites. Common "
        "concerns include Psittacosis (Chlamydiosis), Proventricular Dilatation Disease, and "
        "Pacheco's disease. Household hazards include Teflon/PTFE non-stick cookware fumes "
        "(acutely lethal), scented candles, air fresheners, aerosols, and cigarette smoke. "
        "Symptoms requiring immediate veterinary attention: tail bobbing, sitting on the cage "
        "floor, fluffed feathers with closed eyes, undigested food in droppings, change in "
        "droppings color or consistency, and sudden weight loss (weigh weekly on a gram scale "
        "for early detection). Maintain temperature between 65–85°F and avoid drafts."
    ),
    "guinea_pig_feeding": (
        "Guinea pigs cannot synthesize Vitamin C and require 10–30 mg daily from food — "
        "deficiency causes scurvy within weeks. Excellent sources include fresh bell peppers "
        "(highest C content), parsley, kale, and commercial pellets with stabilized vitamin C "
        "(replace regularly as vitamin C degrades quickly in pellets). The foundation of the "
        "diet is unlimited timothy hay for dental wear and gut motility. Fresh pellets "
        "formulated specifically for guinea pigs (not rabbit pellets) should be provided at "
        "approximately 1/8 cup per day. Offer fresh leafy greens daily. Avoid fruits, starchy "
        "vegetables, and iceberg lettuce (low nutrition, causes diarrhea). Fresh water must "
        "be available at all times; provide both a bottle and a bowl since individuals prefer "
        "different sources."
    ),
    "guinea_pig_exercise": (
        "Guinea pigs need at least 1–2 hours of supervised floor time outside their enclosure "
        "daily in a guinea-pig-proofed space. Unlike hamsters, guinea pigs should never be "
        "placed in exercise balls and do not use wheels — both cause injury and acute stress. "
        "Floor time in a pen with tunnels, hides, and scattered forage opportunities satisfies "
        "natural instincts. Guinea pigs exercise more actively in pairs or groups; a lone animal "
        "often moves less and becomes lethargic. Rearranging the enclosure periodically with new "
        "tunnels and hides maintains novelty and encourages exploration. The enclosure itself "
        "should be at minimum 10.5 square feet for two guinea pigs — C&C cages or similar large "
        "enclosures are strongly recommended, as pet-store hutches are almost always undersized. "
        "Guinea pigs are crepuscular and most active at dawn and dusk; offer enrichment and floor "
        "time during these windows for best engagement."
    ),
    "guinea_pig_grooming": (
        "Short-haired guinea pigs need brushing 1–2 times per week; during shedding seasons "
        "brush more frequently to reduce hair ingestion. Long-haired breeds (Peruvian, Silkie) "
        "require daily combing to prevent painful mats and to keep hair clear of the face and "
        "genitals. Use a soft-bristle brush and small metal comb. Nails must be trimmed every "
        "4–6 weeks; overgrown nails curve and can tear or grow into the foot pad. Bathing is "
        "rarely necessary; when needed, use a guinea-pig-safe shampoo and dry thoroughly — wet, "
        "cold guinea pigs are susceptible to respiratory infections. Check the anal sac (a small "
        "pocket near the anus, more prominent in neutered males) for impaction, which requires "
        "gentle cleaning. Teeth grow continuously; adequate hay prevents most dental problems, "
        "but watch for drooling, food-dropping, or weight loss as early signs of dental disease. "
        "Spot-clean droppings and soiled bedding daily; do a full cage clean at least weekly."
    ),
    "guinea_pig_health": (
        "Guinea pigs are social animals and should ideally be housed with at least one "
        "companion of the same sex; a lone guinea pig requires substantially more owner "
        "interaction to remain emotionally healthy. Common health issues include respiratory "
        "infections (pneumonia is a leading cause of death), urinary tract problems and bladder "
        "stones, dental disease (teeth grow continuously), and vitamin C deficiency. Annual "
        "veterinary exams are recommended, twice-yearly for senior guinea pigs (4+ years). "
        "They are highly sensitive to temperature extremes — keep between 65–75°F and never "
        "in direct sunlight or drafts. Weigh weekly on a kitchen scale; early weight loss is "
        "often the first sign of illness. Signs of illness include reduced appetite, labored "
        "breathing, changes in droppings, or social withdrawal. Average lifespan is 5–7 years."
    ),
    "hamster_feeding": (
        "Hamsters do best on a commercial hamster-specific seed and grain mix or a lab block "
        "diet. Supplement with small amounts of fresh vegetables: leafy greens, broccoli, "
        "and cucumber. Avoid citrus, garlic, onions, tomato, and grapes. Hamsters use cheek "
        "pouches to cache food — check pouches weekly; impacted pouches (where food becomes "
        "stuck) are a veterinary emergency requiring prompt attention. Sugar-containing foods "
        "must be strictly limited as dwarf hamster breeds are genetically prone to diabetes. "
        "Fresh water in a drip bottle should always be available; water bowls tip easily and "
        "cause wet fur. Provide a ceramic or metal food dish — hamsters chew plastic. "
        "Remove perishable food from the enclosure within 24 hours to prevent spoilage."
    ),
    "hamster_exercise": (
        "Hamsters are highly active and can run 5–8 miles per night in the wild — a solid-surface "
        "wheel is a primary welfare need, not an optional accessory. Wheel sizes must match the "
        "species: 10–12 inches for Syrian hamsters, 8 inches for Chinese hamsters, and 6.5–8 "
        "inches for dwarf breeds (Roborovski, Campbell's, Winter White). Wire or mesh wheels "
        "cause bumblefoot (pododermatitis) and limb injuries; only solid-surface or mesh-free "
        "wheels (Niteangel, Silent Runner, Wodent Wheel) are acceptable. Provide tunnels, deep "
        "burrowing substrate (minimum 6 inches), and a sand bath to support natural behaviors. "
        "Exercise balls are not recommended — they cause disorientation, restrict ventilation, "
        "and cause stress; supervised free-roam in a hamster-proofed pen is preferable. Hamsters "
        "are crepuscular to nocturnal; avoid disturbing them during daytime sleep, as disrupted "
        "sleep cycles cause chronic stress and can shorten their already brief lifespan."
    ),
    "hamster_grooming": (
        "Hamsters are fastidious self-groomers and rarely require human grooming intervention. "
        "Short-haired hamsters need no routine brushing. Long-haired (Teddy Bear) Syrian hamsters "
        "may need occasional gentle combing with a soft toothbrush to prevent mats, especially "
        "around the rear end. Always provide a sand bath (chinchilla sand, not dust) for dwarf "
        "breeds — they use it naturally to clean their coats; limit sessions to 10–15 minutes "
        "to prevent dry skin. Never use water baths; hamsters are extremely prone to hypothermia "
        "and shock from bathing. Scent glands (on the flanks in Syrians, on the abdomen in "
        "dwarfs) may appear greasy or waxy — this is normal marking behavior, not a grooming "
        "concern. Check cheek pouches weekly; impacted pouches (food stuck inside) require "
        "immediate veterinary attention. Spot-clean the enclosure 2–3 times per week by removing "
        "soiled bedding and uneaten perishables; do a full clean monthly — over-cleaning removes "
        "scent cues and stresses hamsters, while under-cleaning causes harmful ammonia build-up."
    ),
    "hamster_health": (
        "Hamsters have a short lifespan of 1.5–3 years (Roborovskis up to 3.5 years), so "
        "health changes can appear and progress rapidly. Wet tail (proliferative ileitis) is a "
        "severe, rapidly fatal bacterial diarrhea most common in Syrian hamsters under 12 "
        "weeks or under stress — symptoms are liquid diarrhea and lethargy; this requires "
        "immediate veterinary attention. Dwarf hamster breeds are predisposed to diabetes; "
        "symptoms include excessive thirst and urination, weight loss despite normal eating, "
        "and lethargy. Tumors are common in older hamsters, especially Syrian females. The "
        "enclosure should provide at least 450 square inches of unbroken floor space — smaller "
        "cages cause stereotypic bar-chewing and chronic stress. A solid-surface wheel 10–12 "
        "inches in diameter for Syrians (6.5–8 inches for dwarfs) is essential nightly exercise; "
        "wire or mesh wheels cause foot and leg injuries."
    ),
    "reptile_feeding": (
        "Reptile feeding requirements vary significantly by species and must be researched "
        "specifically for the animal in your care. Insectivores (leopard geckos, young bearded "
        "dragons) require gut-loaded live or frozen-thawed insects dusted with calcium and D3 "
        "supplements 2–5 times weekly. Omnivores like crested geckos thrive on a commercial "
        "fruit-based crested gecko diet (CGD) as their staple, supplemented with occasional "
        "insects; do not treat them as primarily insectivorous. Herbivores and omnivores (adult bearded "
        "dragons, iguanas, tortoises) need dark leafy greens and squash; dandelion greens, "
        "collard greens, and mustard greens are excellent staples. Carnivores (ball pythons, "
        "corn snakes) eat pre-killed or frozen-thawed rodents sized to the snake's girth — "
        "live prey is strongly discouraged due to injury risk. Adult snakes typically feed "
        "every 7–14 days. Calcium supplementation (with D3 for species lacking adequate UVB, "
        "without D3 for those with proper UVB lighting) is essential to prevent metabolic bone "
        "disease."
    ),
    "reptile_exercise": (
        "Reptile activity varies greatly by species but all benefit from enclosures large enough "
        "to allow natural movement and behavioral expression. Arboreal species (chameleons, green "
        "tree pythons, crested geckos) need vertical space with climbing branches and foliage; "
        "inadequate climbing structures cause muscle atrophy and chronic stress. Terrestrial "
        "species (leopard geckos, ball pythons) need floor space, multiple hides, and objects to "
        "explore. Bearded dragons benefit from regular supervised exploration outside the "
        "enclosure in a warm, safe area — they are naturally active and curious when healthy. "
        "Temperature gradients encourage physical movement as reptiles thermoregulate by shifting "
        "between warm and cool zones. UVB-driven circadian rhythms influence activity; inadequate "
        "photoperiods cause lethargy and appetite suppression. Enrichment items — varied substrate "
        "textures, cork rounds, live-safe plants, and additional hides — encourage exploration and "
        "reduce stress behaviors like glass surfing or excessive, abnormal hiding."
    ),
    "reptile_grooming": (
        "Reptiles shed their skin periodically (ecdysis) — healthy sheds come off in large pieces "
        "and snakes should shed in one complete piece. Retained shed (dysecdysis) indicates "
        "incorrect humidity, dehydration, or illness; soak the animal in lukewarm water for "
        "15–20 minutes to loosen it and allow natural removal. Never force-pull retained shed as "
        "it tears live tissue. Providing a humid hide (a hide with damp sphagnum moss inside) "
        "supports successful shedding. Check for retained eye caps (spectacles) after each snake "
        "shed — retained caps require professional or careful removal with a moist cotton swab. "
        "Claw trimming is needed every 4–8 weeks for active lizard species like bearded dragons "
        "and iguanas, but is not typically required for snakes. Enclosure cleaning frequency "
        "depends on the substrate type: bioactive setups need spot-cleaning only; paper or tile "
        "substrates may need full replacement weekly. Disinfect with reptile-safe products "
        "(diluted F10 or similar) — bleach residue is toxic to reptiles."
    ),
    "reptile_health": (
        "Reptiles require highly species-specific husbandry — research each species' exact "
        "temperature gradient, humidity, UVB requirements, and enclosure size before "
        "acquisition. Metabolic Bone Disease (MBD), caused by insufficient calcium or "
        "UVB lighting, is one of the most common preventable illnesses; symptoms include "
        "soft or curved bones, difficulty walking, and jaw deformity. UVB bulbs degrade before "
        "they visibly dim — replace every 6–12 months. Respiratory infections are common when "
        "humidity or temperature is incorrect. Cryptosporidiosis is a serious, sometimes "
        "incurable parasitic disease; quarantine all new reptiles for 90 days. Annual fecal exams by a "
        "reptile-experienced veterinarian are recommended. Signs of illness include wheezing, "
        "mucus around the mouth or nostrils, prolonged refusal to eat, rapid weight loss, and "
        "discharge from the eyes."
    ),
    "fish_feeding": (
        "Most tropical and cold-water fish should be fed once or twice daily, offering only "
        "what they consume in 2–3 minutes. Overfeeding is the leading cause of water quality "
        "problems — uneaten food decomposes and spikes ammonia, which is toxic to fish. Vary "
        "the diet with species-appropriate foods: most tropical fish do well with quality "
        "flake or pellet food supplemented with frozen foods (brine shrimp, daphnia, "
        "bloodworms). Herbivores (plecos, otocinclus) need algae wafers or blanched "
        "vegetables. Carnivores (bettas, cichlids) need protein-rich pellets or frozen foods. "
        "Fasting one day per week benefits most fish by clearing the digestive tract and "
        "reducing waste production. Consider automatic feeders to maintain consistent timing "
        "during travel or irregular schedules."
    ),
    "fish_exercise": (
        "Fish health and behavior depend on adequate swimming space and environmental complexity. "
        "Crowded tanks suppress immune function, increase aggression, and cause chronic stress — "
        "research minimum tank sizes per species, as many commonly sold fish (goldfish, oscar "
        "cichlids) require far more space than pet stores suggest. Provide current flow suited to "
        "the species: rheophilic fish (hillstream loaches, danios) need moderate-to-strong "
        "circulation; slow-water species (bettas, discus) need calmer zones. Enrich the tank with "
        "live or silk plants, caves, driftwood, and varied substrate to give fish territories, "
        "hiding spots, and visual boundaries that reduce aggression. Schooling species (tetras, "
        "danios, corydoras) require groups of 6 or more to feel secure and display natural "
        "behavior; solitary schooling fish are chronically stressed. Monitor swimming patterns "
        "during regular observation — erratic movement, bottom-sitting, surface gasping, or "
        "clamped fins all indicate problems requiring prompt investigation."
    ),
    "fish_grooming": (
        "Aquarium maintenance directly determines fish health. Perform 25–30% water changes "
        "weekly using a gravel vacuum to remove detritus and reduce nitrate accumulation. Clean "
        "algae from the glass with an aquarium scraper or magnetic cleaner — some algae is "
        "beneficial but excess reduces light and oxygen. Rinse filter media monthly in removed "
        "tank water, never tap water, to clear debris while preserving the beneficial bacterial "
        "colony; never replace all filter media at once. Replace degraded mechanical media "
        "(sponge, floss) as needed, but not during the same session as biological media changes. "
        "Clean decorations with a dedicated aquarium brush and avoid all soap or household "
        "cleaners — residue is lethal to fish. Test water parameters after each maintenance "
        "session to confirm stability. A consistent weekly maintenance schedule prevents the "
        "parameter swings that stress fish and trigger disease outbreaks."
    ),
    "fish_health": (
        "Fish health is directly tied to water quality. Test water parameters weekly: ammonia "
        "and nitrite should be 0 ppm; nitrate below 20 ppm for most species; pH appropriate "
        "to the species (most tropical fish: 6.8–7.5). Perform 25–30% water changes weekly "
        "using a gravel vacuum to remove detritus. Cycle new tanks fully before adding fish "
        "(4–8 weeks) to establish the beneficial bacterial colony. Common illnesses include "
        "ich (white spots — treat with heat or medication), fin rot (ragged fins from poor "
        "water quality or aggression), and velvet (gold-dust appearance). Quarantine all new "
        "fish for 2–4 weeks before introducing them to an established tank. An appropriately "
        "sized filter, heater (for tropical fish), and test kits are essential equipment. "
        "Crowding increases stress and disease — research each species' space requirements."
    ),
}

_EXERCISE_KEYWORDS = {"walk", "walking", "exercise", "run", "jog", "hike", "play", "playing", "fetch", "agility", "sport", "roam", "free-roam", "forage", "enrichment", "perch", "fly", "flight", "wheel", "tunnel", "burrow", "climb", "training", "scratch"}
_FEEDING_KEYWORDS = {"feed", "feeding", "food", "meal", "breakfast", "dinner", "lunch", "treat", "water", "eating", "pellet", "hay", "insect", "cricket", "worm", "mouse", "rat", "seed", "flake", "vegetable", "veggie", "greens", "fruit", "supplement", "prey", "rodent", "wafer", "bloodworm", "kibble"}
_GROOMING_KEYWORDS = {"brush", "groom", "grooming", "bath", "bathe", "trim", "nail", "coat", "fur", "shampoo", "comb", "cage", "tank", "bedding", "litter", "clean", "teeth", "dental", "ear", "shed", "shedding", "beak", "wing", "preen", "mist", "filter", "gravel", "algae"}
_HEALTH_KEYWORDS = {"vet", "vaccine", "medicine", "medication", "health", "checkup", "doctor", "pill", "shot", "insulin", "wound", "flea", "tick", "heartworm", "parasite", "mite", "calcium", "uvb", "vitamin", "spay", "neuter", "respiratory", "urinary", "quarantine", "stasis", "booster", "dewormer"}

# Maps selectbox values to knowledge base key prefixes (handles multi-word species names)
_SPECIES_KEY_MAP: dict[str, str] = {
    "guinea pig": "guinea_pig",
}


def retrieve_relevant_chunks(
    species_list: list[str],
    task_names: list[str],
    max_chunks: int = 4,
) -> list[tuple[str, str]]:
    """Return (chunk_key, chunk_text) tuples most relevant to the given species and tasks."""
    normalized_species = [s.lower().strip() for s in species_list]
    task_words = {
        stripped
        for name in task_names
        for w in name.split()
        if (stripped := w.lower().strip(".,!?;:'\"()[]"))
    }

    # Scheduling entries are most relevant for multi-pet or complex schedules; prepend them
    # so they are never pushed out of the max_chunks budget by species-specific candidates.
    candidates: list[str] = []
    if len(species_list) >= 2 or len(task_names) >= 5:
        candidates.append("general_scheduling")
        candidates.append("task_prioritization")

    for species in normalized_species:
        species_key = _SPECIES_KEY_MAP.get(species, species)
        if task_words & _EXERCISE_KEYWORDS:
            candidates.append(f"{species_key}_exercise")
        if task_words & _FEEDING_KEYWORDS:
            candidates.append(f"{species_key}_feeding")
        if task_words & _GROOMING_KEYWORDS:
            candidates.append(f"{species_key}_grooming")
        if task_words & _HEALTH_KEYWORDS:
            candidates.append(f"{species_key}_health")

    seen: set[str] = set()
    unique: list[str] = []
    for key in candidates:
        if key not in seen and key in KNOWLEDGE_BASE:
            seen.add(key)
            unique.append(key)

    if not unique:
        unique = ["general_scheduling", "task_prioritization"]

    return [(key, KNOWLEDGE_BASE[key]) for key in unique[:max_chunks]]
