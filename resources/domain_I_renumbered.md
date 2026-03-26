# Domain I: Creating Accessible Web Solutions (40%)

I.A.
## I.A. Guidelines, Principles, and Techniques for Meeting Success Criteria
I.A..1
**Compare** the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.


### WCAG 2.2
I.A..2
**Explain** the structure of WCAG 2.2 by identifying the four principles (POUR), guidelines, and success criteria levels (A, AA, AAA).

I.A..3
**Differentiate** between normative and non-normative parts of WCAG and **justify** why that distinction matters for conformance.

I.A..4
**Apply** W3C-recommended techniques (e.g., sufficient techniques, failure techniques) to specific WCAG success criteria in real coding scenarios.

I.A..5
**Summarize** the rationale for using the latest WCAG 2.2 and **evaluate** the impact of new success criteria (e.g., Focus Not Obscured) on website design.


### WAI-ARIA 1.2
I.A..6
**Differentiate** between normative and non-normative parts of WAI-ARIA and **justify** why that distinction matters for conformance.

I.A..7
**Explain** the purpose and impact of WAI-ARIA 1.2 on web accessibility

I.A..8
**Describe** the WAI-ARIA 1.2 model of roles, states, and properties

I.A..9
**Determine** when to use WAI-ARIA 1.2 versus standard HTML elements

I.A..10
**Apply** the five rules for using ARIA correctly


### ATAG 2.0
I.A..11
**Differentiate** between normative and non-normative parts of ATAG and **justify** why that distinction matters for conformance.

I.A..12
**Explain** how ATAG 2.0 applies to web content authoring tools

I.A..13
**Describe** the meaning and intent of the two main sections of ATAG 2.0 (Part A: Accessible user interface; Part B: Supporting accessible content production)

I.A..14
**Distinguish** between automated accessibility practices in authoring tools and practices requiring author/user input

I.A..15
**Evaluate** the power and limitations of automated accessibility authoring features

I.A..16
**Differentiate** between normative and non-normative information in ATAG 2.0


### EN 301 549
I.A..17
**Identify** the types of technologies addressed by EN 301 549

I.A..18
**Compare** and contrast the similarities and differences between WCAG and EN 301 549

I.A..19
**Explain** how WCAG is represented in EN 301 549

I.A..20
**Identify** requirements beyond WCAG that are relevant for compliance with the Web Accessibility Directive 2016/2102

I.A..21
**Interpret** the self-scoping (applicability) language used in EN 301 549

I.A..22
**Explain** the intent and scope of EN 301 549 requirements that extend beyond WCAG


I.B.
## I.B. Basic Knowledge of Programming
I.B..1
**Demonstrate** how JavaScript event handlers can be made device-independent (e.g., supporting both pointer and keyboard input).

I.B..2
**Explain** progressive enhancement and **outline** the implications of turning JavaScript off or using older browsers for accessibility.

I.B..3
**Identify** common pitfalls in dynamic content updates (e.g., partial page refreshes with AJAX) and **implement** focus management or live regions to keep screen reader users informed.

I.B..4
**Distinguish** between semantic HTML controls (e.g., `<button>`, `<a>`) and generic elements (e.g., `<div>`) in terms of built-in accessibility.

I.B..5
**Analyze** how focus order, event handling (onClick, onKeyDown, etc.), and ARIA states can either improve or harm the user experience for assistive technology.


### Imported Objectives (From objectives_export.md)
I.B..6
Analyze how JavaScript implementations can either improve or reduce accessibility and usability for people using assistive technologies.

I.B..7
Compare the accessibility implications of applying JavaScript event handlers (such as onclick) to semantic elements (e.g., `<a>` or `<button>`) versus non-semantic elements (e.g., `<div>`).

I.B..8
Determine appropriate focus management techniques for moving focus to newly revealed or dynamically generated content.


I.C.
## I.C. Create Interactive Controls/Widgets Based on Best Practices
I.C..1
**Construct** a custom widget (e.g., a modal dialog or accordion) using the WAI-ARIA Authoring Practices, ensuring correct roles, states, and properties.

I.C..2
**Demonstrate** correct keyboard interaction models (e.g., tab vs. arrow keys) for composite components such as menus, tabs, and disclosure widgets.

I.C..3
**Evaluate** existing custom controls for missing or incorrect ARIA markup, and **recommend** solutions to align them with best practices.


### Imported Objectives (From objectives_export.md)
I.C..4
Analyze accessibility of interactive components and ARIA-based widgets based on expected keyboard and screen reader behavior.

I.C..5
Analyze interactive components to ensure they support single-pointer alternatives for gesture-based interactions.

I.C..6
Apply established keyboard interaction conventions when testing ARIA-based custom widgets.

I.C..7
Apply established keyboard interaction models when implementing ARIA-based custom widgets, including the use of Tab to enter widgets and arrow keys to navigate within them.

I.C..8
Apply standard keyboard interaction models when designing and implementing ARIA-based custom widgets.

I.C..9
Evaluate accessibility of interactive components based on keyboard navigation and screen reader behavior.

I.C..10
Evaluate implementations of custom widgets to determine whether they follow established accessibility authoring practices.

I.C..11
Evaluate when native HTML controls should be used instead of custom ARIA widgets based on accessibility best practices and implementation complexity.


I.D.
## I.D. Using ARIA
I.D..1
**Explain** the five primary rules of ARIA usage (e.g., "use native HTML first," "do not change native semantics unless necessary").

I.D..2
**Implement** accessible names and descriptions using `aria-label`, `aria-labelledby`, and `aria-describedby`, and **justify** which approach is most appropriate in a given scenario.

I.D..3
**Demonstrate** correct focus management using `aria-activedescendant` or roving `tabindex` in interactive widgets.

I.D..4
**Analyze** how the accessibility tree is exposed to assistive technology and **verify** ARIA roles, states, and properties in different screen reader/browser combinations.


### Imported Objectives (From objectives_export.md)
I.D..5
Analyze accessibility implications of complex web applications and determine how ARIA roles, states, and properties can communicate interface changes to assistive technologies.

I.D..6
Analyze web interface patterns to determine when WAI-ARIA is appropriate.

I.D..7
Analyze widget implementations to determine whether appropriate WAI-ARIA roles, states, and properties are applied correctly.

I.D..8
Apply ARIA live region properties to announce dynamically added content without moving keyboard focus when appropriate.

I.D..9
Apply ARIA properties and states to communicate widget state and dynamic changes in user interfaces (e.g., checked, expanded).

I.D..10
Apply techniques for providing accessible names and descriptions to interactive controls and widgets.

I.D..11
Compare the accessibility benefits and limitations of native HTML controls and custom WAI-ARIA widgets.

I.D..12
Describe the semantic structure of ARIA roles, including required parent roles, child roles, and associated attributes.

I.D..13
Describe the WAI-ARIA roles, states, and properties model and how it communicates semantics to assistive technologies.

I.D..14
Determine appropriate use of ARIA live regions to notify assistive technologies of dynamic content updates.

I.D..15
Evaluate different techniques for notifying assistive technologies when dynamic content changes occur, including the use of ARIA live regions and related mechanisms.

I.D..16
Evaluate scenarios where the application role may be used and justify when it should be avoided due to its impact on assistive technology keyboard navigation.

I.D..17
Evaluate whether native HTML semantics or WAI-ARIA should be used in a given implementation scenario.

I.D..18
Explain how assigning an ARIA role overrides the native semantic role of an HTML element and the implications this has for accessibility APIs and assistive technologies.

I.D..19
Explain the five rules for using ARIA and their importance in accessible interface design.

I.D..20
Explain the purpose of WAI-ARIA and its role in improving accessibility for dynamic web content and custom interface components.

I.D..21
Explain the role of the accessibility tree in conveying semantic information from web content to assistive technologies.

I.D..22
Identify appropriate ARIA roles used to describe interactive widgets (e.g., menu, treeitem, slider, progressbar) and structural elements of a page (e.g., headings, regions, tables).


I.E.
## I.E. Accessibility-Supported Technologies
I.E..1
**Identify** how assistive technologies (e.g., screen readers, magnifiers, voice input) interact with browsers and what "accessibility-supported" means under WCAG.

I.E..2
**Assess** the compatibility of a chosen technology stack (front-end framework, JS library) with major screen reader/browser pairs and **recommend** fallback or polyfill strategies.

I.E..3
**Explain** how touch interaction changes with a screen reader turned on (e.g., iOS VoiceOver gestures) and **demonstrate** design patterns to support these gestures.


### Imported Objectives (From objectives_export.md)
I.E..4
Analyze accessibility issues to determine whether they result from design or implementation flaws versus limitations in browser or assistive technology support.

I.E..5
Distinguish between accessibility features that can be implemented automatically by authoring tools and those requiring author input.

I.E..6
Evaluate the capabilities and limitations of automated accessibility support within authoring tools.

I.E..7
Evaluate unexpected screen reader behavior to determine whether it results from accessibility issues in the web content, limitations in assistive technology support, or incorrect testing techniques.

I.E..8
Explain how ARIA can enhance assistive technology support for dynamic content and custom user interface components.


I.F.
## I.F. Standard Controls vs. Custom Controls
I.F..1
**Compare** native HTML controls' built-in accessibility features with custom (ARIA-based) components, highlighting pros and cons.

I.F..2
**Demonstrate** how to repurpose a non-semantic element into a fully accessible custom button or link using proper ARIA attributes, keyboard events, and visible focus.

I.F..3
**Recommend** standard HTML controls whenever possible and **justify** the business and user benefits of reducing custom code for accessibility.


I.G.
## I.G. Single-Page Applications (SPAs)
I.G..1
**Demonstrate** how to manage announcements of dynamic page updates (e.g., with `aria-live`) when navigation or content changes do not trigger a full page reload.

I.G..2
**Implement** focus changes appropriately when new views or dialogs appear, ensuring screen-reader and keyboard-only users can track SPA updates.

I.G..3
**Evaluate** the user experience of a single-page application with typical assistive technologies and **propose** solutions for any discovered gaps.


### Imported Objectives (From objectives_export.md)
I.G..4
Analyze dynamic content updates in SPAs to determine whether users should be notified when new content is loaded.

I.G..5
Evaluate touch interfaces to confirm that touch targets are large enough and sufficiently spaced.

I.G..6
Explain accessibility challenges associated with single-page applications (SPAs), including focus management, dynamic content updates, and assistive technology compatibility.

I.G..7
Test single-page application behaviors with screen readers to verify that asynchronous content updates are correctly announced and accessible.

I.G..8
Test whether focus indicators, labels, and instructions remain visible and usable at increased zoom levels or modified text spacing.


I.H.
## I.H. Strategies of Persons with Disabilities in Using Web Solutions
I.H..1
**Describe** key strategies that users with blindness, low vision, motor disabilities, auditory disabilities, and cognitive/learning disabilities employ to interact with web content.

I.H..2
**Analyze** design elements (e.g., headings, landmarks, color contrast) to determine their impact on diverse user groups' navigation and comprehension strategies.

I.H..3
**Propose** layout or structural revisions (e.g., skip links, consistent navigation) that accommodate multiple disability groups.
