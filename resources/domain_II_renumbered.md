# Domain II: Identify Accessibility Issues in Web Solutions (40%)

### Imported Objectives (From objectives_export.md)

II.A.
## II.A. Interoperability and Compatibility Issues
II.A..1
**Identify** potential issues arising from specific browser–screen reader combinations (e.g., JAWS + Chrome vs. NVDA + Firefox).

II.A..2
**Explain** why certain ARIA roles or HTML5 elements might not be fully supported across older browsers, and how to mitigate these gaps.

II.A..3
**Evaluate** a website's accessibility across multiple devices (desktop, tablet, mobile) and assistive technologies.


### Imported Objectives (From objectives_export.md)
II.A..4
Analyze how accessibility support changes when assistive technologies are combined with different user agents.

II.A..5
Analyze how users with disabilities interact with web content using assistive technologies, adaptive strategies, and user agents.

II.A..6
Describe how assistive technologies interact with user agents, including browsers and applications.

II.A..7
Explain how web content, user agents (browsers and media players), assistive technologies, and authoring tools interact to provide an accessible web experience.


II.B.
## II.B. Identifying Guidelines and Principles Regarding Issues
II.B..1
**Map** discovered accessibility barriers to the appropriate WCAG success criterion (or EN 301 549 clause) and **distinguish** conformance failures from best-practice gaps.

II.B..2
**Apply** the WCAG-EM methodology to define scope, explore site content, select a representative sample, and evaluate conformance thoroughly.

II.B..3
**Explain** the concept of conformance levels (A, AA, AAA) and **defend** the rationale for choosing a specific level in a project or legal context.

II.B..4
**Describe** the limitations in WCAG (e.g., certain gaps for cognitive or motion-based issues) and **propose** best-practice enhancements.


### Imported Objectives (From objectives_export.md)
II.B..5
Analyze accessibility issues to determine whether they represent failures of WCAG Success Criteria or broader usability or accessibility concerns not explicitly covered by the specifications.

II.B..6
Analyze differences in how assistive technology users may interact with web content based on skill level, navigation strategies, and personal preferences.

II.B..7
Analyze dynamic content updates to determine when keyboard focus should be moved to newly loaded content.

II.B..8
Analyze examples of web content to determine whether they meet or fail specific WCAG success criteria.

II.B..9
Analyze the scope and intent of the requirements listed in Annex A, Table A.1 in EN 301 549 that go beyond WCAG.

II.B..10
Apply standard keyboard interaction patterns to test native HTML interactive elements.

II.B..11
Apply the WCAG Evaluation Methodology (WCAG-EM) to systematically evaluate the accessibility of web content.

II.B..12
Assess caption accuracy and completeness to ensure that automatic captioning errors have been corrected.

II.B..13
Assess form fields to ensure appropriate autocomplete attributes are implemented where relevant.

II.B..14
Classify WCAG 2.2 Success Criteria according to their conformance levels (A, AA, AAA).

II.B..15
Compare the accessibility requirements in EN 301 549 with those defined in WCAG.

II.B..16
Describe the purpose and scope of the two primary sections of ATAG 2.0.

II.B..17
Describe the relationship between WCAG principles, guidelines, and success criteria.

II.B..18
Differentiate between accessibility issues that can be detected by automated tools and those that require manual evaluation.

II.B..19
Differentiate between sufficient techniques, advisory techniques, and failures associated with WCAG success criteria.

II.B..20
Differentiate between the disciplines of accessibility and user experience (UX) design, including their goals, assumptions, and areas of overlap.

II.B..21
Distinguish between normative and non-normative information within accessibility specifications.

II.B..22
Explain factors that influence the selection of a target accessibility conformance level (e.g., legal requirements, organizational policies, or project goals).

II.B..23
Explain how ATAG 2.0 applies to web content authoring tools and development environments.

II.B..24
Explain how WCAG requirements are incorporated into EN 301 549.

II.B..25
Explain the intent and accessibility impact of each WCAG principle.

II.B..26
Explain WCAG conformance requirements and how they apply to evaluating web content.

II.B..27
Identify additional accessibility requirements in EN 301 549 that extend beyond WCAG.

II.B..28
Identify relevant accessibility requirements in specifications such as WCAG 2.2, WAI-ARIA, and ATAG when evaluating accessibility issues.

II.B..29
Identify the technologies and digital products addressed by EN 301 549.

II.B..30
Identify WCAG 2.2 Success Criteria and their associated conformance levels (A, AA, AAA).

II.B..31
Interpret the intent and requirements of ATAG principles, guidelines, and success criteria.

II.B..32
Interpret the requirements of WCAG success criteria and their implications for accessible design and development.

II.B..33
Summarize the major additions introduced in WCAG 2.1, particularly those addressing new input methods and improved support for low vision and cognitive disabilities.


II.C.
## II.C. Testing with Assistive Technologies
II.C..1
**Conduct** screen reader testing to confirm that name, role, value, and state changes of interactive elements are conveyed properly.

II.C..2
**Demonstrate** manual keyboard testing to detect missing focus indicators, incorrect tab order, or keyboard traps.

II.C..3
**Use** magnifier or high-contrast settings to **detect** any text or interface elements that become unusable or unreadable.

II.C..4
**Identify** common user needs for auditory disabilities (e.g., accurate captions, transcripts) and evaluate if they are met.


### Imported Objectives (From objectives_export.md)
II.C..5
Evaluate focus management, focus order, and visibility of focus indicators during keyboard navigation.

II.C..6
Evaluate form implementations based on expected screen reader interaction patterns.

II.C..7
Evaluate HTML markup to verify that semantic structure (e.g., headings, lists, tables, and landmarks) correctly conveys meaning to assistive technologies.

II.C..8
Evaluate keyboard operability, focus order, and link descriptions to ensure they support effective screen reader navigation.

II.C..9
Evaluate navigation structures, headings, and labels to determine whether they provide clear and consistent information architecture.

II.C..10
Evaluate responsive behavior to ensure content adapts to different viewport sizes without requiring two-dimensional scrolling.

II.C..11
Evaluate scenarios where it may be appropriate to supplement or override browser or assistive technology behavior to improve accessibility, while considering potential risks and compatibility impacts.

II.C..12
Evaluate the limitations of accessibility guidelines, principles, and techniques when assessing real-world accessibility issues.

II.C..13
Evaluate web content to determine whether text alternatives are provided for images, video, and other non-text content.

II.C..14
Evaluate web implementations to ensure accessibility solutions follow established web standards rather than relying on technology-specific quirks.

II.C..15
Test character-key shortcuts to ensure they can be disabled, remapped, or activated only when the relevant component has focus.

II.C..16
Test dynamic content updates to confirm that roles, names, values, and status messages are communicated to screen readers using appropriate ARIA attributes or live regions.

II.C..17
Test the reading order of web content to confirm that the programmatic order is meaningful and consistent with the intended visual presentation.

II.C..18
Test web interfaces to confirm that all functionality can be operated using a keyboard without keyboard traps.

II.C..19
Verify that error messages are programmatically associated with form fields and that clear instructions and suggestions for correction are provided.

II.C..20
Verify that page language, form errors, and component states are programmatically conveyed to assistive technologies.


II.D.
## II.D. Testing Tools for the Web
II.D..1
**Compare** the strengths and limitations of automated tools, browser-based linters, spider tools, and bookmarklets for accessibility testing.

II.D..2
**Use** at least one site-wide scanning tool and one browser-based developer tool (e.g., Axe, WAVE, Lighthouse) to **detect** markup or ARIA errors.

II.D..3
**Interpret** automated test results to confirm valid failures, eliminate false positives, and plan follow-up manual checks.


### Imported Objectives (From objectives_export.md)
II.D..4
Analyze accessibility issues identified by testing tools and determine appropriate follow-up manual testing strategies.

II.D..5
Analyze automated accessibility testing results to identify false positives, omissions, and issues requiring manual verification.

II.D..6
Analyze how accessibility testing tools can be applied at different stages of the web development lifecycle, including design, development, and testing.

II.D..7
Analyze how accessibility testing tools can be integrated at different stages of the web development lifecycle, including design, development, and testing.

II.D..8
Evaluate the strengths and limitations of automated accessibility testing tools.

II.D..9
Explain the purpose of Accessibility Conformance Testing (ACT) Rules and their role in standardizing automated accessibility testing.

II.D..10
Identify common categories of accessibility testing tools, including site-wide scanning tools, server-based analysis tools, unit and integration testing tools, browser developer tools, browser extensions, simulators, and guided manual testing tools.

II.D..11
Inspect HTML structure and accessibility attributes using browser developer tools to identify potential accessibility issues.

II.D..12
Inspect HTML structure and accessibility-related attributes using browser developer tools.


II.E.
## II.E. Accessibility Quality Assurance
II.E..1
**Explain** how accessibility can be integrated into agile vs. waterfall lifecycles, focusing on early detection of issues.

II.E..2
**Establish** a continuous testing process (automated + manual) that catches regressions after updates or new releases.

II.E..3
**Coordinate** with product owners, designers, and developers to incorporate accessibility checks into acceptance criteria and "definition of done."


### Imported Objectives (From objectives_export.md)
II.E..4
Analyze development workflows to determine how accessibility practices can be incorporated into ongoing quality assurance and regression testing processes.

II.E..5
Compare Agile and Waterfall project management methodologies and analyze how each approach incorporates accessibility quality assurance activities.

II.E..6
Explain how accessibility considerations should be integrated throughout the product development lifecycle, including concept, requirements, design, prototyping, development, quality assurance, user testing, support, and regression testing.

II.E..7
Explain how accessibility maturity models and assessment tools can be used to measure progress and support long-term accessibility sustainability.


II.F.
## II.F. Testing with Assistive Technologies (Extended)
II.F..1
**Demonstrate** usage of at least two popular screen reader/browser combinations (e.g., NVDA + Firefox, VoiceOver + Safari) to confirm consistent user experience.

II.F..2
**Verify** that dynamically updated or hidden elements are properly announced or hidden from screen readers.

II.F..3
**Assess** whether alternative input methods (switch control, voice input) can navigate and operate interactive elements effectively.


### Imported Objectives (From objectives_export.md)
II.F..4
Evaluate whether interactive elements are implemented using native controls or appropriate ARIA semantics to support voice control and alternative input devices.

II.F..5
Identify issues for users who use keyboard or alternative input devices.


II.G.
## II.G. Testing for End-User Impact (Low Vision, Cognitive, Mobile/Touch)
II.G..1
**Perform** usability walk-throughs with simulated low-vision settings (zoom, high contrast) to find layout or text-flow issues.

II.G..2
**Assess** mobile interaction (touch gestures, orientation changes) to **ensure** elements remain accessible and do not require two-dimensional scrolling.

II.G..3
**Identify** potential cognitive barriers (e.g., complex language or form instructions) and **recommend** simpler language or multi-step guidance.


### Imported Objectives (From objectives_export.md)
II.G..4
Evaluate motion-based interactions to ensure they can be disabled and replaced with accessible controls.

II.G..5
Evaluate multimedia content to verify that captions are provided for video and transcripts are available for audio-only content.

II.G..6
Evaluate the impact of contrast enhancement modes (such as Windows High Contrast Mode) on the presentation and usability of web interfaces.

II.G..7
Evaluate time limits, moving content, and automatically playing media to determine whether users can control or disable them.

II.G..8
Explain how touch-based interactions change when screen readers are enabled on mobile devices.

II.G..9
Identify accessibility issues related to sensory-dependent instructions, automatically playing audio, or moving content that may interfere with screen reader use.

II.G..10
Test device orientation support to ensure content and functionality are available in both portrait and landscape orientations.

II.G..11
Test mobile interfaces to confirm that all functionality available on desktop viewports is also accessible on smaller touch screens.

II.G..12
Test web interfaces for sufficient text and non-text contrast.

II.G..13
Understand the principles of color contrast requirements in web accessibility and evaluate when and how they apply to ensure text and visual elements are perceivable to users with visual impairments.

II.G..14
Verify that gesture-based interactions provide accessible single-pointer alternatives.

II.G..15
Verify that motion-based or device-motion interactions provide accessible alternative controls.

II.G..16
Verify that text can be resized up to 200% without loss of functionality or content.


II.H.
## II.H. Testing Tools for the Web (Revisited)
II.H..1
**Demonstrate** how to use color-contrast analyzers, focus inspectors, or code validators to confirm partial compliance with WCAG criteria.

II.H..2
**Explain** how ACT Rules can guide consistent test procedures across multiple tools and testers.
