# Saved-Graph Tutor Conversation

- Objective: Evaluate web content to determine whether text alternatives are provided for images, video, and other non-text content.
- Student turns: 14
- Tutor model: gpt-5.4
- Reasoning model: gpt-5.4
- Started: 2026-04-28T18:00:50.281551

## Turn 1

- Stage: introduction -> introduction
- Active graph node after: n1
- Elapsed: 31.62s

### Student

I need to evaluate whether non-text content has good alternatives. I know images sometimes need alt text, but I am not sure how to decide what counts as good or when something should be ignored.

### Tutor

Start with one rule: don’t ask “does it have text?” first; ask “what purpose is this non-text content serving here?” Under WCAG 1.1.1, the alternative is good if it serves the equivalent purpose in context, and if the content is pure decoration, only visual formatting, or not meant to be understood by users, it should be implemented so assistive technology can ignore it rather than announcing it. So a useful image needs text that gives the same needed information, a control image needs a name that tells what it does, and a decorative border should be ignored instead of described.

Try this case: a magnifying-glass image that opens search when clicked — would a good alternative describe how it looks, or what it does?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n1",
  "next_node_id": "",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "Stay on n1 because the student is still forming the core decision rule, confusion is medium, and concept closure is not ready; the student's question should be answered within the current node before any advance.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Answer the student's question directly, but keep the explanation anchored to the current concept that non-text content requires a text-equivalent decision. Clarify that the key criterion is the content's purpose, use a few contrasting examples to distinguish when an alternative is useful versus when content should be ignored by assistive technology, and then return to checking the student's understanding of the purpose-first decision rule.",
  "analyzer_feedback": ""
}
```

## Turn 2

- Stage: introduction -> introduction
- Active graph node after: n2
- Elapsed: 39.26s

### Student

I think maybe it should say what it looks like, like “magnifying glass,” since that tells the user what the icon is? But because it opens search, maybe “search icon” or just “search” is better. I’m still a little unsure when the appearance matters versus the action.

### Tutor

Use action when the image is functioning as a control. For controls or input, WCAG’s equivalent-purpose idea means the name should tell the user what the control does, so “Search” is better than “magnifying glass,” because the job of that image is to start search, not to teach its shape. Appearance matters more when the image’s purpose is to convey visual information itself, not trigger an action.

Try a contrast: if the same magnifying-glass image appeared inside an article explaining common interface symbols, would you still name it by action, or by what it shows?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n2",
  "next_node_id": "n3",
  "active_edge_id": "n1->n2",
  "allowed_teaching_move": "clarify_current_node",
  "decision_reason": "Advance from n1 to n2 because the student has enough evidence that non-text content requires evaluation, but keep instruction focused on n2 since the purpose-versus-appearance distinction is still fragile and concept closure for n2 is not ready.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Answer the student's question directly while anchoring the explanation to n2: clarify when an image alternative should reflect appearance versus purpose, use a few contrastive examples that separate functional controls from purely descriptive cases, and then briefly recheck the student's understanding of the purpose-first rule before moving on.",
  "analyzer_feedback": ""
}
```

## Turn 3

- Stage: introduction -> introduction
- Active graph node after: n2
- Elapsed: 38.94s

### Student

I think in the article case I’d switch to what it shows, like “magnifying glass icon” or maybe “search symbol,” because the point is the symbol itself, not clicking it. Although now I’m wondering if “search symbol” sneaks the action back in too much. Is the test basically “what would be lost if the image wasn’t visible?”

### Tutor

Yes — that’s a very good working test. Ask: if the image were not visible, what would a user lose here: information, function, or nothing important? If they’d lose meaningful information or a function, the alternative should preserve that purpose; if they’d lose nothing but visual styling, it should be ignored by assistive technology.

For example, if a page has a photo next to a news story and the photo adds information to the story, hiding it would remove something meaningful; if the same area just has a flourish or border, hiding it changes the look but not the meaning.

Using that test, if an image is a leaf pattern used only as a visual divider between sections, what would you decide?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n2",
  "next_node_id": "n3",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "The student shows strong progress on n2, but concept closure is only almost ready and the pending boundary check still needs confirmation before advancing.",
  "accepted_analyzer_recommendation": false,
  "override_reason": "I am narrowing the analyzer's advance recommendation because the active concept is not fully closed yet. The student\u2019s question is productive, but the evidence still indicates a fragile boundary between informative and decorative cases.",
  "tutor_directive": "Answer the student's question directly using the current node focus: confirm and refine the 'what would be lost if hidden' test with one or two contrastive examples, then do a brief check that the student can use purpose-in-context to distinguish when an image needs meaningful equivalent information versus when it does not. Do not fully introduce n3 yet; use this as closure for n2.",
  "analyzer_feedback": "When recommending advance, require concept_closure to be clearly ready rather than almost_ready. A resolved-candidate misconception plus a pending boundary check suggests remaining fragility, so prefer a closure move before transitioning."
}
```

## Turn 4

- Stage: introduction -> introduction
- Active graph node after: n4
- Elapsed: 50.02s

### Student

I’d call that decorative, so I think it should be ignored by assistive tech, like empty `alt=""` if it’s an `img`, or maybe better as a CSS background if it’s really just styling. Since removing it wouldn’t take away info or function, describing “leaf pattern divider” would just add noise, right? What if the divider is also kind of thematic and helps signal a change of topic visually — is that still decorative?

### Tutor

Yes—if it only adds mood or visual styling, it can still be decorative, even if it feels thematic. The boundary is this: if hiding the divider would remove meaningful information about the content’s structure or topic change, then it is not pure decoration; if it only makes the transition look nicer, it stays decorative and should be ignored by assistive technology. Under WCAG 1.1.1, pure decoration or visual formatting is the case that should be implemented so assistive tech can ignore it; once it’s actually conveying information, it needs an equivalent alternative instead.

Try a contrast: if a flower graphic appears between two sections, but the page already has clear text headings showing the new topic, would you treat that flower graphic as decorative or informative?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n4",
  "next_node_id": "n5",
  "active_edge_id": "",
  "allowed_teaching_move": "clarify_current_node",
  "decision_reason": "The prior active concept is sufficiently closed, and the student's boundary-case question now squarely targets the decorative-vs-informative distinction in n4. No must-repair issue remains on n2, but n4 still needs one clarifying pass before mastery.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Advance the focus to n4. Answer the student's question directly as a decorative-versus-informative boundary case, using purpose-in-context and the loss-if-hidden test. Clarify that if the divider only adds visual styling it remains decorative, but if hiding it would remove meaningful structure or topic-change information, it is not merely decorative. Then do one brief check on a contrasting example before moving on.",
  "analyzer_feedback": ""
}
```

## Turn 5

- Stage: introduction -> introduction
- Active graph node after: n4
- Elapsed: 233.3s

### Student

I’d treat it as decorative, since the headings are already doing the real structure/topic-change work. So I think the flower shouldn’t get announced, because otherwise it’s just extra noise. But if there were no headings and the flower was the only cue that a new section started, would that mean the design is kind of broken accessibility-wise even if I tried to give the flower alt text?

### Tutor

Yes: if the flower is the only cue that a new section starts, then it is not decorative, because hiding it would remove meaningful information. In that case, “flower” would not be a good alternative—the text would need to convey the purpose of that cue, not just its appearance. From the evidence we’re using, the key judgment is that this image would need an equivalent text alternative rather than being ignored.

Now push that one step further: if an image is clickable and takes you to Search, should its text alternative name what it looks like or what it does?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n4",
  "next_node_id": "n5",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "The student shows strong transfer on n4, but there is still an open edge-case question tied to the current concept. That question should be answered on n4 before advancing to n5.",
  "accepted_analyzer_recommendation": false,
  "override_reason": "Narrowing the analyzer's advance recommendation because answer_current_question_first is true and the active gap is still within the decorative-vs-informative boundary on n4. Advance can happen immediately after this answer if no new confusion appears.",
  "tutor_directive": "Answer the student's section-cue question as a boundary case within n4, making clear whether the image is decorative or informative based on whether hiding it would remove meaningful structure. After answering, do one very brief confirmation check and then bridge to n5.",
  "analyzer_feedback": "When recommending advance, treat an unresolved boundary-case question within the active node as a reason to stay temporarily, even when concept_closure is otherwise ready. Distinguish 'ready after one direct answer' from 'ready to advance immediately.'"
}
```

## Turn 6

- Stage: introduction -> introduction
- Active graph node after: n5
- Elapsed: 37.66s

### Student

What it does, so I’d label it “Search” rather than “magnifying glass.” I think I’m finally seeing the pattern: for controls, the accessible name should match the function, not the visual. Edge case though: if the icon is inside a button that already has visible text like “Search,” do I just make the image decorative then?

### Tutor

Yes — if the button already has visible text like “Search,” and that text gives the button’s purpose, the icon is usually redundant and should be treated so assistive technology can ignore it. The button still needs an accessible name that describes its purpose, but the icon itself does not need to add “magnifying glass” or a second “Search” if the text label already does that job. So this is the same rule again: name the function once, and hide redundant imagery from assistive tech.

Fresh case: a button shows a trash-can icon with visible text “Delete” next to it — how would you treat the icon?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n5",
  "next_node_id": "n5",
  "active_edge_id": "n4->n5",
  "allowed_teaching_move": "introduce_next_node",
  "decision_reason": "The student's open question is a functional-image edge case, n4 is sufficiently closed, and the analyzer evidence supports moving into n5 to answer and practice the new concept.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Bridge from decorative images to functional images by treating the student's labeled-button icon question as the entry point to n5. Answer the edge case within n5, then give one brief fresh control example to check function-vs-appearance naming and redundant-icon treatment.",
  "analyzer_feedback": ""
}
```

## Turn 7

- Stage: introduction -> introduction
- Active graph node after: n6
- Elapsed: 44.14s

### Student

I’d treat the trash-can icon as decorative, since the visible text “Delete” already gives the button’s function. So I’d hide the icon from assistive tech and let the button name come from the text. Is that basically true for any icon + text combo, or are there cases where the icon still carries extra meaning?

### Tutor

Not always: if the visible text already gives the control’s purpose, the icon is redundant and should be ignored by assistive technology, but if the icon adds extra information the text does not give, then it is not decorative. A good test is “what would be lost if the icon were hidden?” If extra meaning would be lost, that meaning needs an equivalent in text rather than being ignored.

Now shift to a different kind of case: if a chart image has far more information than a short alt text can realistically carry, what do you think that suggests about the kind of text alternative it needs?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n6",
  "next_node_id": "n6",
  "active_edge_id": "n5->n6",
  "allowed_teaching_move": "introduce_next_node",
  "decision_reason": "Analyzer evidence indicates n5 is ready for closure: the student shows solid transfer, low confusion, no open misconception, and only needs a brief boundary clarification before moving on.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Briefly answer the student's icon+text boundary question to close n5, emphasizing the distinction between redundant icons and icons that add extra meaning, then transition into n6 by introducing the idea that some visuals are too complex for a short alternative alone.",
  "analyzer_feedback": ""
}
```

## Turn 8

- Stage: introduction -> introduction
- Active graph node after: n7
- Elapsed: 37.71s

### Student

I think that means a short `alt` alone isn’t enough, and the chart needs a longer text alternative somewhere, like adjacent text, a data table, or a more detailed description on the page. Maybe the `alt` should just identify the chart briefly and point to the fuller explanation, instead of trying to cram everything in. Is that the idea — short alt for the type/purpose, then the actual data/trends in surrounding text?

### Tutor

Yes—and if you switch from complex images to media, how would you classify a prerecorded podcast with no video: audio-only, video-only, or synchronized media?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n7",
  "next_node_id": "n7",
  "active_edge_id": "n6->n7",
  "allowed_teaching_move": "introduce_next_node",
  "decision_reason": "Analyzer evidence shows n6 is ready for closure: the student correctly explains the short-label-plus-longer-explanation pattern for complex images, shows transferable reasoning, and no misconception or confusion remains.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Briefly confirm the student's formulation of the complex-image pattern to close n6, then transition to n7 by introducing that alternatives for media depend on whether the content is audio-only, video-only, or synchronized audio-video.",
  "analyzer_feedback": ""
}
```

## Turn 9

- Stage: introduction -> introduction
- Active graph node after: n7
- Elapsed: 33.12s

### Student

That would be audio-only, since there’s no visual track to sync with anything. So for a prerecorded podcast I’d expect a text alternative/transcript rather than captions, because captions are more for video timing, right? Or do we still talk about captions if the audio player has no video at all?

### Tutor

Yes — for prerecorded audio-only media like a podcast, the expected pattern is an alternative for time-based media that presents equivalent information, so your “transcript/time-based text alternative rather than captions” idea is the right direction. In the evidence here, captions are the requirement for synchronized media’s audio content, not for prerecorded audio-only by itself. So the deciding factor is the media type: audio-only gets a time-based alternative; synchronized media gets captions for its audio.

Try the contrast: if you have a prerecorded silent demo video with no audio track at all, would you treat that like audio-only, video-only, or synchronized media?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n7",
  "next_node_id": "",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "Stay on n7 because the student shows solid progress but concept closure is not ready yet; the open clarification about audio-only alternatives should be answered and the student still needs comparison across video-only and synchronized media.",
  "accepted_analyzer_recommendation": false,
  "override_reason": "Analyzer recommended advance, but the active concept still has an open pending check and is only almost_ready, not ready for closure.",
  "tutor_directive": "Answer the student's question about prerecorded audio-only by confirming the applicable alternative pattern, then return to n7 and prompt a side-by-side contrast of audio-only, video-only, and synchronized media with one concrete example each before assessing mastery.",
  "analyzer_feedback": "When concept_closure is almost_ready and the lesson_state shows a pending check within the active node, recommend staying on the current node rather than advancing, even if the student's latest answer is correct."
}
```

## Turn 10

- Stage: introduction -> introduction
- Active graph node after: n7
- Elapsed: 33.47s

### Student

I’d treat that as video-only, since there’s no audio to synchronize with anything. So I think it would need a text alternative that describes what’s shown or the steps/action in the demo, kind of like the video equivalent of a transcript. If it’s just decorative motion or doesn’t add info beyond nearby text, does that change it?

### Tutor

Yes — if that silent prerecorded video truly adds no information beyond nearby text, then the evaluation turns on purpose in context, not just the file type. If it is only decorative, WCAG’s decorative-content path applies: content that is pure decoration or only aesthetic should be implemented so assistive technology can ignore it, rather than needing an equivalent alternative. But if the motion is actually showing steps, state changes, or any information the nearby text does not already give, then it is still prerecorded video-only and needs an equivalent alternative for that visual information.

So try this contrast: a prerecorded product clip has spoken narration and matching visuals, versus a live webinar with speech and slides — which one is prerecorded synchronized media and which one is live synchronized media?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n7",
  "next_node_id": "",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "Stay on n7 because the student has a solid but not yet closed grasp of the active concept, and there is still an open pending check on edge-case classification and the contrast with synchronized and live media.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Answer the student's edge-case question directly within n7, then return to the active concept and prompt a concise contrast between prerecorded video-only, prerecorded synchronized media, and live synchronized media, including what alternative or captioning pattern applies to each, before assessing mastery.",
  "analyzer_feedback": ""
}
```

## Turn 11

- Stage: introduction -> introduction
- Active graph node after: n8
- Elapsed: 33.16s

### Student

The prerecorded product clip sounds like prerecorded synchronized media, because it has audio and visual parts that go together. The live webinar with speech and slides would be live synchronized media. I think the key is both have synchronized audio + visuals, but the timing of when it’s delivered changes which requirement path you check — is that the right way to separate them?

### Tutor

Yes — that’s the right separator. Both are synchronized media because they combine audio and visuals, and the delivery timing is what separates prerecorded from live for the requirement path.

Now the next step is not just “is there some alternative,” but “is the alternative actually useful.” Imagine a prerecorded tutorial video has captions, but the captions only say “[music]” and miss all the spoken instructions. Would you judge that as meeting the need, or as text being present but not actually equivalent?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n8",
  "next_node_id": "n8",
  "active_edge_id": "n7->n8",
  "allowed_teaching_move": "introduce_next_node",
  "decision_reason": "Advance from n7 to n8 because the analyzer shows concept closure is ready on the active media-classification concept, confusion is low, no misconception requires repair, and the remaining gap is now evaluation of alternative quality.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Briefly answer the student's confirmation question about prerecorded versus live synchronized media, close n7, and then introduce n8 by giving one example that asks the student to judge whether provided captions, a transcript, or a description is accurate and useful.",
  "analyzer_feedback": ""
}
```

## Turn 12

- Stage: introduction -> introduction
- Active graph node after: n8
- Elapsed: 35.12s

### Student

I’d judge that as failing the need, because captions exist technically but they’re not equivalent to the spoken instructions at all. So in an evaluation I think I’d note “text alternative present, but inadequate/incomplete,” not count it as passing just because a captions track is there. Is the right test basically “could someone who can’t hear still get the same instructional info from the captions/transcript?”

### Tutor

Yes — that’s the right test. For this objective, the question is whether the provided captions or transcript convey the same instructional information in context, not whether some text track merely exists. Under WCAG 1.1.1’s “equivalent purpose” idea, incomplete or placeholder-like text does not count as a true alternative.

Try one fresh case: an image next to a recipe shows the finished cake covered in strawberries, and its alt text is just “image123.jpg” — would you treat that as an adequate alternative or as text present but not useful, and why?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n8",
  "next_node_id": "",
  "active_edge_id": "",
  "allowed_teaching_move": "answer_student_question_then_return",
  "decision_reason": "Stay on n8 because the student shows solid understanding but concept closure is only almost ready, and the active node still has an open transfer check before advancing.",
  "accepted_analyzer_recommendation": false,
  "override_reason": "The analyzer recommended advance, but its own evidence says n8 is still in progress, concept_closure is almost_ready rather than ready, and the student still needs at least one fresh usefulness/equivalence judgment on a new case.",
  "tutor_directive": "Briefly confirm the student's equivalence test question, then return to n8 with one fresh example requiring the student to judge whether a provided alternative is accurate and useful; do not introduce n9 yet.",
  "analyzer_feedback": "When concept_closure is almost_ready and the pending check explicitly requires another transfer example on the current concept, recommend staying on the active node rather than advancing."
}
```

## Turn 13

- Stage: introduction -> introduction
- Active graph node after: n9
- Elapsed: 39.79s

### Student

I’d treat that as text present but not useful, so basically a fail for the image alternative. “image123.jpg” doesn’t communicate the image’s purpose or content at all, and definitely not what a user would get visually from seeing the finished strawberry cake. I think I’d write something like “photo of finished cake topped with strawberries” if the image is informative, but if the recipe text already fully describes the final appearance, is there ever a case where the image could be treated as decorative instead?

### Tutor

Yes — if the nearby recipe text already fully provides the same information and the image adds no new information or function, you can treat it as decorative in that context; if it adds information users are meant to get from seeing it, it is not decorative. A decorative item should be implemented so assistive technology can ignore it, while an informative one needs an equivalent text alternative. On a page with three items — a border flourish image with null alt, a chart with alt “Sales chart” and a full explanation in the next paragraph, and a silent prerecorded demo video with only the filename “demo-final.mp4” nearby — which one fails, and at what step in the identify-pattern-judge process?

### Graph Decision

```json
{
  "graph_action": "advance",
  "active_node_id": "n9",
  "next_node_id": "",
  "active_edge_id": "n8->n9",
  "allowed_teaching_move": "introduce_next_node",
  "decision_reason": "Advance from n8 to n9 because the analyzer shows n8 is ready for closure, confusion is low, no misconception requires repair, and the remaining work is integrated application across mixed cases.",
  "accepted_analyzer_recommendation": true,
  "override_reason": "",
  "tutor_directive": "Briefly answer the student's decorative-vs-informative context question, then transition into n9 by giving one mixed non-text case where the student must identify the content type, choose the appropriate alternative pattern, and judge whether the provided alternative is adequate.",
  "analyzer_feedback": ""
}
```

## Turn 14

- Stage: introduction -> introduction
- Active graph node after: n9
- Elapsed: 31.4s

### Student

I think the one that clearly fails is the silent prerecorded demo video, because when I identify the pattern it’s video-only, then at the judge step the only “alternative” is basically just a filename, which isn’t equivalent at all.  

The border flourish with null alt sounds fine if it’s truly decorative, so that passes at the purpose/context check. The chart one feels a little trickier, but if the next paragraph really gives the full explanation, I’d probably say it passes overall even though the alt text alone is super minimal, because the equivalent info exists in context.  

Am I using the steps right if I say: identify content type first, then check whether it’s decorative/functional/informative in context, then judge whether the provided text alternative is actually equivalent?

### Tutor

Yes — that’s the right process. I’d tighten one detail: after identifying the content type, you match it to the right requirement path for that kind of content, and then you judge whether the provided alternative is actually equivalent in context.

One last transfer check: a page has a magnifying-glass image used as the Search button, and its alt text is “magnifier icon.” At which step does that fail, or does it pass?

### Graph Decision

```json
{
  "graph_action": "stay",
  "active_node_id": "n9",
  "next_node_id": "",
  "active_edge_id": "",
  "allowed_teaching_move": "assess_mastery",
  "decision_reason": "The student appears ready for closure on n9, but the lesson state still calls for one fresh transfer check before ending the node, so remain on n9 and assess mastery there.",
  "accepted_analyzer_recommendation": false,
  "override_reason": "I am narrowing the analyzer's advance recommendation because n9 is the terminal active concept on the route and the pending check specifies one final mixed transfer case before closure rather than advancing to a new node.",
  "tutor_directive": "Briefly confirm that the student's identify-pattern-judge sequence is correct, then give one fresh mixed non-text scenario with minimal scaffolding to test transfer. Use the student's response to assess mastery of the full evaluation process on n9.",
  "analyzer_feedback": "When the active node is the final route node and evidence supports readiness, prefer an assess-on-current-node recommendation over advance unless a specific next node or integration target exists."
}
```
