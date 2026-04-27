# Teaching Graph: Evaluate Text Alternatives for Non-Text Content

## Objective

Evaluate web content to determine whether text alternatives are provided for images, video, and other non-text content.

## Plain-Language Goal

The learner should be able to inspect common non-text content, decide whether it needs a text alternative, judge whether the provided alternative is appropriate for the content's purpose, and explain when a missing or poor alternative creates an accessibility failure.

## Graph Type

decision_application

This objective is a decision-and-evaluation task. The learner must classify the type and purpose of non-text content, decide what kind of alternative is required, and evaluate real examples rather than only recalling a definition.

## Primary Route

1. `n1`: Non-text content needs a text-equivalent decision
2. `n2`: Purpose determines the right alternative
3. `n3`: Informative images need equivalent information
4. `n4`: Decorative images should be ignored by assistive technology
5. `n5`: Functional images need a purpose-based name
6. `n6`: Complex images need a short label plus longer explanation
7. `n7`: Audio and video alternatives depend on media type and content
8. `n8`: Evaluate provided alternatives for accuracy and usefulness
9. `n9`: Apply the full non-text-content evaluation process

## Nodes

### `n1`: Non-text content needs a text-equivalent decision

**Kind:** support_prerequisite

**Teachable claim:** Non-text content must be evaluated to determine whether users need a text alternative to receive the same information or function.

**Learner must understand:**

- Non-text content includes images, controls, charts, media, CAPTCHA, and other non-text forms.
- The evaluator should not only ask whether an `alt` attribute exists.
- The key question is what information or function the content provides.

**Common misconception:** Accessibility checking for images means only checking whether every image has an `alt` attribute.

**Likely retrieval need:** High. This node needs a normative anchor for non-text content and text alternatives.

### `n2`: Purpose determines the right alternative

**Kind:** core_concept

**Teachable claim:** The correct text alternative depends on why the non-text content is present in context.

**Learner must understand:**

- The same image can require different alternatives in different contexts.
- The alternative should communicate the content's purpose, not merely describe pixels.
- Context matters when judging whether an alternative is sufficient.

**Common misconception:** A text alternative should always be a literal visual description.

**Likely retrieval need:** High. This node needs explanatory evidence and examples showing context-sensitive alternatives.

### `n3`: Informative images need equivalent information

**Kind:** core_concept

**Teachable claim:** If an image communicates information, the text alternative should provide the same meaningful information to users who cannot perceive the image.

**Learner must understand:**

- Informative images are part of the content, not decoration.
- A useful alternative conveys the relevant information or meaning.
- Vague alternatives like "image" or "graphic" usually do not provide equivalent information.

**Common misconception:** Any non-empty alt text is acceptable for an informative image.

**Likely retrieval need:** High. This node needs examples of sufficient and insufficient alternatives.

### `n4`: Decorative images should be ignored by assistive technology

**Kind:** core_concept

**Teachable claim:** If an image is purely decorative and provides no information or function, it should have a null text alternative or otherwise be ignored by assistive technology.

**Learner must understand:**

- Decorative content should not create unnecessary noise.
- A null alternative is different from a missing alternative.
- Decoration is determined by context, not by image file type.

**Common misconception:** Every image must have descriptive alt text, even if it is decorative.

**Likely retrieval need:** High. This node needs direct evidence for null alternatives and decorative images.

### `n5`: Functional images need a purpose-based name

**Kind:** core_concept

**Teachable claim:** If an image acts as a control or link, its text alternative should describe the function or destination, not the image's appearance.

**Learner must understand:**

- Functional images are evaluated like controls or links.
- The alternative should answer what action the user can take.
- A visual description may fail if it does not communicate the function.

**Common misconception:** A linked icon's alt text should describe the icon shape rather than the link purpose.

**Likely retrieval need:** High. This node needs technique or example evidence for functional images and links/buttons.

### `n6`: Complex images need a short label plus longer explanation

**Kind:** core_concept

**Teachable claim:** Complex non-text content, such as charts, diagrams, and maps, often needs a brief alternative plus a longer text explanation that communicates the data or relationships.

**Learner must understand:**

- A short label can identify the image.
- Complex information may require nearby text, a long description, table data, or another equivalent explanation.
- The alternative must support the same understanding, not just name the chart.

**Common misconception:** A chart can be made accessible with alt text that only says "chart."

**Likely retrieval need:** High. This node needs examples or techniques for complex images and long descriptions.

### `n7`: Audio and video alternatives depend on media type and content

**Kind:** core_concept

**Teachable claim:** Time-based media may require captions, audio description, transcripts, or media alternatives depending on whether the content is audio-only, video-only, prerecorded, live, or synchronized media.

**Learner must understand:**

- Images and media are both non-text content, but they often require different alternative formats.
- Captions, transcripts, and audio description solve different access needs.
- The evaluator must identify the media type before deciding what is required.

**Common misconception:** A transcript is always enough for every video accessibility requirement.

**Likely retrieval need:** Medium to high. This node needs media-related anchors without expanding too far beyond the objective.

### `n8`: Evaluate provided alternatives for accuracy and usefulness

**Kind:** core_concept

**Teachable claim:** A text alternative must be judged for whether it accurately and usefully communicates the content's meaning or function in context.

**Learner must understand:**

- Present-but-poor alternatives can still fail the purpose of text alternatives.
- Repetition, vagueness, wrong function, or missing key information can make an alternative insufficient.
- Evaluation requires comparing the alternative to the content's role in the page.

**Common misconception:** If an automated scanner finds an alt attribute, the image has passed.

**Likely retrieval need:** High. This node needs failure or evaluation evidence showing why presence alone is not enough.

### `n9`: Apply the full non-text-content evaluation process

**Kind:** integration

**Teachable claim:** Effective evaluation follows a repeatable process: identify the non-text content, determine its purpose and type, choose the required alternative pattern, and judge whether the actual alternative provides equivalent information or function.

**Learner must understand:**

- Different content types require different evaluation questions.
- The same page can contain decorative, informative, functional, complex, and media examples.
- The final judgment should explain both the issue and the expected fix.

**Common misconception:** Text-alternative evaluation can be reduced to one universal rule for all non-text content.

**Likely retrieval need:** Medium. The integration node can reuse node evidence but needs a realistic mixed example.

## Edges

### `n1` -> `n2`

**Type:** prerequisite

**Bridge claim:** Before evaluating any alternative, the learner must decide what purpose the non-text content serves in context.

**Transition question:** What is this content doing for the user on this page?

**Likely retrieval need:** Low. The connected nodes should provide enough support.

### `n2` -> `n3`

**Type:** applies_to

**Bridge claim:** When the purpose is informational, the alternative must communicate the information that the image contributes.

**Transition question:** If the image teaches or communicates something, what would a non-visual user need to know?

**Likely retrieval need:** Medium. Example evidence may help ground the distinction.

### `n2` -> `n4`

**Type:** contrasts_with

**Bridge claim:** Decorative content is the contrast case: if the image has no information or function, adding descriptive text can be harmful noise.

**Transition question:** When is the best alternative no spoken text at all?

**Likely retrieval need:** Medium. This edge benefits from contrastive evidence between informative and decorative images.

### `n2` -> `n5`

**Type:** applies_to

**Bridge claim:** When the purpose is functional, the alternative should name the action or destination rather than visual appearance.

**Transition question:** What will the user do if they activate this image?

**Likely retrieval need:** Medium. Functional-image examples are useful here.

### `n3` -> `n6`

**Type:** refines

**Bridge claim:** Complex images are a special case of informative images where a short text alternative may not carry all necessary information.

**Transition question:** When is a short alt value not enough to communicate the information?

**Likely retrieval need:** Medium to high. This edge should retrieve complex-image or long-description support if node evidence is thin.

### `n6` -> `n8`

**Type:** supports

**Bridge claim:** Complex examples show why evaluation must judge usefulness and completeness, not just the existence of text.

**Transition question:** Does this alternative let the user understand the same data or relationship?

**Likely retrieval need:** Low to medium. Node evidence can probably support this.

### `n7` -> `n8`

**Type:** supports

**Bridge claim:** Media alternatives reinforce that each alternative must be evaluated against the access need it is meant to satisfy.

**Transition question:** Does this transcript, caption, or description solve the right access problem?

**Likely retrieval need:** Medium. Media-specific evidence may be useful if the final example includes media.

### `n8` -> `n9`

**Type:** synthesizes_into

**Bridge claim:** Accuracy and usefulness checks become the final evaluation process across all non-text content types.

**Transition question:** What sequence of checks should you apply to a mixed page with several kinds of non-text content?

**Likely retrieval need:** Medium. Integration retrieval should support a realistic mixed-page evaluation scenario.

## Suggested Teaching Sequence

### Stage 1: Establish the evaluation question

Teach `n1` and `n2`.

Start with a page containing several images and ask what each item is doing: informing, decorating, linking, explaining complex data, or presenting media.

### Stage 2: Classify image purpose

Teach `n3`, `n4`, and `n5`.

Use three simple cases:

```html
<img src="warning.png" alt="Warning: account will be locked after three failed attempts">
<img src="border-flourish.png" alt="">
<a href="/cart"><img src="cart.png" alt="View cart"></a>
```

The goal is to show that the right alternative changes with purpose.

### Stage 3: Handle complex non-text content

Teach `n6`.

Use a chart or diagram example where the learner decides what belongs in the short label and what requires a longer explanation or adjacent data.

### Stage 4: Extend beyond static images

Teach `n7`.

Introduce audio-only, video-only, and synchronized media at a high level. Keep this focused on choosing the right alternative format, not every media success criterion in depth.

### Stage 5: Evaluate quality, not just presence

Teach `n8`.

Compare alternatives that are missing, present but vague, misleading, overly verbose, or correctly matched to purpose.

### Stage 6: Full mixed-page evaluation

Teach `n9`.

Give a realistic page with decorative imagery, an informative chart, an image link, and a short video. The learner should classify each item and explain what alternative is required or whether the current alternative is sufficient.

## Retrieval Implications

The graph suggests three retrieval layers.

### Node Retrieval

Node retrieval should gather factual anchors for each non-text-content category.

High-priority nodes:

- `n1`: normative anchor for non-text content and text alternatives
- `n2`: context/purpose-driven alternative selection
- `n3`: informative image alternatives
- `n4`: decorative image null alternatives
- `n5`: functional image alternatives
- `n6`: complex image alternatives and longer descriptions
- `n8`: evaluation/failure evidence showing present-but-poor alternatives can fail

Medium-priority node:

- `n7`: media alternative anchors, kept compact so the lesson does not become a full media-accessibility lesson

Lower-priority node:

- `n9`: can mostly reuse earlier node evidence, plus one mixed scenario

### Edge Retrieval

Edge retrieval should be selective.

Edges that may need their own retrieval:

- `n2` -> `n4`: contrastive evidence showing why decorative images should be ignored rather than described
- `n2` -> `n5`: functional-image evidence where the alternative names the function
- `n3` -> `n6`: complex-image evidence where a short alternative alone is insufficient
- `n8` -> `n9`: support for applying multiple evaluation checks in a mixed scenario

Edges that probably do not need fresh retrieval:

- `n1` -> `n2`
- `n2` -> `n3`
- `n6` -> `n8`
- `n7` -> `n8`

### Integration Retrieval

Integration retrieval should support one realistic mixed-page evaluation.

A strong final example should include:

- one informative image with a useful alternative
- one decorative image with a null alternative
- one functional image link or button
- one chart or diagram requiring longer explanation
- one audio or video item requiring the correct alternative format
- at least one failure where an alternative exists but is not useful

The model can write the final scenario and teaching explanation, but factual claims about required alternatives, decorative handling, functional images, complex images, media alternatives, and failures should come from retrieved WCAG/WAI evidence.

## Final Graph Summary

This graph treats text-alternative evaluation as a classification and judgment process. Retrieval should not dump every media and image technique blindly. It should ground the main decision categories, retrieve contrastive edge evidence where the categories are easy to confuse, and use integration retrieval for a realistic mixed-page evaluation task.
