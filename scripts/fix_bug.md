### Pattern
bug_fix

### Language
Swift

### Issue 
Comment /* ... */ is not correct

### RULES

1. Remove all comments in the array including /* 14 */ and /* 15 */
2. Remove any leading whitespace of each string
3. Capitalize the first character of each string (only the first character).
4. Keep everything else exactly the same — punctuation, spelling, and order.

```swift
private let text = [
    /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
    /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
    /* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.",
    /* 4 */ "Dixit Dominus: Ex Basan convertam, convertam in profundum maris.",
    /* 5 */ "Ut intingatur pes tuus in sanguine; lingua canum tuorum ex inimicis ab ipso.",
    /* 6 */ "Viderunt ingressus tuos, Deus, ingressus Dei mei, regis mei, qui est in sancto.",
    /* 7 */ "Praevenerunt principes conjuncti psallentibus, in medio juvencularum tympanistriarum.",
    /* 8 */ "In ecclesiis benedicite Deo Domino, de fontibus Israel.",
    /* 9 */ "Ibi Benjamin adolescentulus, in mentis excessu; ",
    "principes Juda, duces eorum; principes Zabulon, principes Nephthali.",
    /* 10 */ "Manda, Deus, virtuti tuae; confirma hoc, Deus, quod operatus es in nobis.",
    /* 11 */ "A templo tuo in Ierusalem, tibi offerent reges munera.",
    /* 12 */ "Increpa feras arundinis; congregatio taurorum in vaccis populorum, ut excludantur qui probati sunt argento;",
    " Dissipa gentes quae bella volunt. Venient legati ex Aegypto; Aethiopia praeveniet manus eius Deo.",
    /* 14 */ "Regna terrae, cantate Deo; psallite Domino.",
    /* 15 */ "Psallite Deo, qui ascendit super caelum caeli ad orientem; ",
    "ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.",
    /* 17 */ "Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus."
  ]