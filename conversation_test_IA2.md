
======================================================================
[TURN 1] STUDENT:
Hey, I need to learn WCAG structure for my cert exam. I know it's about accessibility but that's about it.

[TURN 1] TUTOR: (6.8s | tokens: 7144/433)
Great — we’ll build it step by step. Quick check to anchor us: in your own words, what do you think WCAG is for (what job does it do on the web)?

======================================================================
[TURN 2] STUDENT:
Umm, it makes websites accessible? Like rules for making things work for disabled people?

[TURN 2] TUTOR: (10.4s | tokens: 7211/774)
You’ve got the gist. WCAG is a standard that sets testable requirements so web content is accessible, and “conformance” means satisfying those requirements.

Now, the structure starts at the top with four big categories called principles (POUR). These are the highest level:
- Perceivable
- Operable
- Understandable
- Robust

They’re like four “buckets” every requirement falls into. Quick check: if a requirement says “Make all functionality available from a keyboard,” which principle would you put that under: Perceivable, Operable, Understandable, or Robust? Why?

======================================================================
[TURN 3] STUDENT:
Perceivable? Because the user needs to be able to perceive that the keyboard works?

[TURN 3] TUTOR: (6.8s | tokens: 7363/442)
I see why you went with Perceivable—if you can’t perceive something, you can’t use it. Here’s the key distinction: Perceivable is about content being presented to your senses (can you see/hear it?), while Operable is about being able to use the interface (can you operate it?). “Make all functionality available from a keyboard” sits under Operable (Guideline 2.1 Keyboard Accessible).

Try this to lock it in: “Provide text alternatives for images.” Which principle does that belong to, and why?

======================================================================
[TURN 4] STUDENT:
That's Perceivable — because it's about making sure the user can perceive the content. A blind user can't see the image, so the text alternative makes it perceivable.

[TURN 4] TUTOR: (9.7s | tokens: 7519/646)
Imagine you’re scanning WCAG and you see both of these items:
- “1.1 Text Alternatives”
- “1.1.1 Non-text Content”

Without looking anything up, which one sounds like the broader goal and which one sounds like the specific check? What makes you think so?

======================================================================
[TURN 5] STUDENT:
1.1 Text Alternatives sounds like the broader one — it's more general. And 1.1.1 Non-text Content sounds like a specific rule under it. Like the .1 at the end makes it more specific? But I don't know what WCAG calls these two levels.

[TURN 5] TUTOR: (7.9s | tokens: 7646/500)
Your instinct is right. WCAG calls “1.1 Text Alternatives” a guideline (a broad goal), and “1.1.1 Non-text Content” a success criterion (a specific, testable requirement under that guideline). Only success criteria are testable and carry conformance levels (A/AA/AAA)—for example, 1.1.1 is Level A.

Say it back in your own words: what’s the difference between a guideline and a success criterion, and which one carries conformance levels?

======================================================================
[TURN 6] STUDENT:
A guideline is a broad goal like 'provide text alternatives' and a success criterion is a specific testable rule under it like 'non-text content must have a text alternative.' Only success criteria have levels. But I still don't get what the levels mean — like what IS Level A vs Level AA?

[TURN 6] TUTOR: (13.2s | tokens: 7822/1055)
Great question. Here’s the core idea: each success criterion is tagged with a conformance level—A, AA, or AAA. Those levels are tiers of conformance. For example:
- 1.1.1 Non-text Content is Level A.
- 1.4.3 Contrast (Minimum) is Level AA.
- 2.4.12 Focus Not Obscured (Enhanced) is Level AAA.

Seeing the label tells you which tier that requirement belongs to.

Your turn: When you see “2.4.12 … Level AAA” next to “2.4.11 … Level AA,” what does that level label tell you about 2.4.12 compared to 2.4.11?

======================================================================
[TURN 7] STUDENT:
Level AAA means it's a harder or more strict requirement? Like AAA is the premium version and A is the basic version? So if you want to be really accessible you need to pass all the AAA ones?

[TURN 7] TUTOR: (10.2s | tokens: 8022/787)
Good instinct to think “stricter,” but two clarifications:
- The level is a tier label attached to each success criterion. It doesn’t mean “more important,” it marks how demanding/feasible the requirement is.
- AAA exists as an upper tier, but it isn’t the default target. Many conformance claims focus on A or AA, and AAA is additional.

Try this reasoning check: if a page passes 2.4.11 Focus Not Obscured (Minimum) (Level AA) but fails 1.1.1 Non‑text Content (Level A), do you think that page can claim Level AA conformance? What’s your rationale?

======================================================================
[TURN 8] STUDENT:
Well it passed the AA one so... maybe? It has at least some AA criteria passing. I'm not sure if failing an A criterion matters for AA.

[TURN 8] TUTOR: (9.5s | tokens: 8200/624)
Makes sense to wonder—but here’s the rule that decides it: to claim Level AA, a page has to satisfy all applicable Level A and Level AA success criteria. Failing any A-level SC means you can’t claim A or AA. Think of it like a ladder: you can’t stand on the AA rung if the A rung below it is missing.

Quick check: If a page meets all Level A SC but fails one Level AA SC, what level of conformance can it legitimately claim? Why?

======================================================================
[TURN 9] STUDENT:
It can claim Level A because it passes all A criteria. It can't claim AA because it's missing one AA criterion. The ladder thing makes sense. Hey but quick side question — what about WCAG 3.0? Is that going to replace all of this?

[TURN 9] TUTOR: (10.0s | tokens: 8365/630)
Good side note. For your certification, focus on WCAG 2.2—the 2.x family shares the same layered structure we’re learning, and that’s what exams typically target. Let’s get back to structure.

Scope next: Do you think WCAG conformance is claimed for an entire site at once, or is it made per web page (individual pages/views)? For example, could a site claim “AA on the homepage, A on product pages,” or does that not make sense under WCAG? Explain your reasoning.

======================================================================
[TURN 10] STUDENT:
I'd guess it's for the whole site? Like you'd say 'our website is WCAG AA compliant' not 'this page is AA but that page is A'. That would be weird.

[TURN 10] TUTOR: (8.8s | tokens: 8520/450)
Totally reasonable guess—most people hear site-wide claims. But WCAG defines conformance at the web page level. A “web page” is a single resource at one URI plus the resources it renders with (like an SPA view at one URL). So, a conformance claim is accurate only for the page(s) in scope; you can claim a whole site only if every page in that scope meets the level.

Try applying that: if only the homepage meets WCAG 2.2 Level AA and product pages meet only Level A, how would you word an accurate conformance claim?

======================================================================
[TURN 11] STUDENT:
You'd have to say the homepage conforms to Level AA and the product pages conform to Level A. You can't just say the whole site is AA. Makes sense now. Okay one thing I keep hearing about is 'WCAG techniques' — are those part of the requirements too?

[TURN 11] TUTOR: (12.3s | tokens: 8706/769)
Good to ask. Short answer: the requirement you must meet is the success criterion in the WCAG spec (for example, 1.4.3 Contrast (Minimum), Level AA). “Techniques” (like G18: ensuring 4.5:1 contrast) are documented ways to meet a success criterion—they’re guidance, not the requirement itself. You can use them, or any other method that satisfies the success criterion.

Say it back: in your own words, what’s the relationship between a success criterion like 1.4.3 and a technique like G18?

======================================================================
[TURN 12] STUDENT:
The success criterion is the rule you have to pass, like having enough contrast. And techniques like G18 are the official ways to pass it — like you have to follow at least one of the listed techniques to conform?

[TURN 12] TUTOR: (10.7s | tokens: 8879/722)
That’s a common assumption, and it makes sense because techniques look “official.” The requirement you must meet is the success criterion text; techniques like G18 are documented ways to meet it (often marked “sufficient”), but you’re not limited to them. If you achieve the same outcome by another method, you still conform because conformance is judged against the SC (e.g., 1.4.3 Contrast (Minimum), Level AA), not against a checklist of techniques.

So if your team uses a custom theming system to ensure 4.5:1 contrast without following G18 verbatim, do you conform to 1.4.3? Why?

======================================================================
[TURN 13] STUDENT:
Yes, you conform because what matters is meeting the success criterion — having 4.5:1 contrast ratio. How you get there doesn't matter as long as the outcome satisfies the SC. Techniques are helpful guides, not requirements.

[TURN 13] TUTOR: (7.0s | tokens: 9071/529)
Let’s decode the numbering. Look at “2.5.7 Dragging Movements.” Based on the pattern you noticed with 1.1 and 1.1.1, what do the numbers 2, 5, and 7 tell you about where this sits—specifically, which principle and which guideline does it belong to?

======================================================================
[TURN 14] STUDENT:
2 is Operable, 5 is the guideline number under Operable, and 7 is the specific success criterion. So it's Principle 2 Operable, Guideline 2.5, SC number 7. I think I've got the whole structure now — can you test me on it?

[TURN 14] TUTOR: (9.0s | tokens: 9212/641)
Let’s do a focused check with a real SC. Suppose a page fails 1.4.3 Contrast (Minimum). Assuming all Level A success criteria pass, what is the highest WCAG 2.2 conformance level that page can legitimately claim, and why?

======================================================================
[TURN 15] STUDENT:
1.4.3 is Level AA. If the page fails it but passes all Level A criteria, the highest it can claim is Level A. It can't claim AA because it's missing an AA criterion, and AA requires all A plus all AA.

[TURN 15] TUTOR: (8.5s | tokens: 9327/544)
Nice work. Quick pivot to where you look things up: you find two resources for 1.4.3 Contrast (Minimum)—the WCAG 2.2 specification page for 1.4.3, and the “Understanding 1.4.3”/Techniques like G18. Which of those actually determines pass/fail for conformance, and which is there to help you apply it? Why?

======================================================================
[TURN 16] STUDENT:
The spec page for 1.4.3 determines pass/fail — that's the actual requirement. The Understanding doc and techniques like G18 help you figure out how to meet it, but they're informative, not normative. Conformance is against the SC, not the techniques.

[TURN 16] TUTOR: (9.5s | tokens: 9478/684)
You’ve just seen that 1.1.1 Non-text Content appears in WCAG 2.0, 2.1, and 2.2, while 2.4.11 Focus Not Obscured (Minimum) is new in 2.2. What does that suggest: did WCAG 2.2 change the overall structure, or did it add/update success criteria within the same Principles → Guidelines → Success Criteria framework? Why do you think so?

======================================================================
[TURN 17] STUDENT:
It added new success criteria within the same structure. The framework stayed the same — POUR principles, guidelines, success criteria with levels. 2.2 just added more SC like 2.4.11. The hierarchy didn't change.

[TURN 17] TUTOR: (8.3s | tokens: 9633/624)
Exactly—WCAG 2.2 kept the same Principles → Guidelines → Success Criteria structure and added/updated some SC within it (like 2.4.11 at Level AA). You’ve pieced together the key distinctions: only success criteria are testable and carry levels, levels are per SC, and AA includes all A. Conformance is claimed per web page, and techniques (like G18) help but aren’t the requirement.

Last consolidation: in 3–4 sentences, summarize WCAG 2.2’s structure and conformance in your own words—name the four principles, say which layer is testable, explain how A/AA/AAA work (including “AA includes all A”), and include one example of placing an SC (e.g., where 1.4.3 fits).
