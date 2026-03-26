# Domain I: Creating Accessible Web Solutions (40%)
## I.A. Guidelines, Principles, and Techniques for Meeting Success Criteria
1. **Compare** the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.
### WCAG 2.2
2. **Explain** the structure of WCAG 2.2 by identifying the four principles (POUR), guidelines, and success criteria levels (A, AA, AAA).
3. **Differentiate** between normative and non-normative parts of WCAG and **justify** why that distinction matters for conformance.
4. **Apply** W3C-recommended techniques (e.g., sufficient techniques, failure techniques) to specific WCAG success criteria in real coding scenarios.
5. **Summarize** the rationale for using the latest WCAG 2.2 and **evaluate** the impact of new success criteria (e.g., Focus Not Obscured) on website design.
### WAI-ARIA 1.2
6. **Differentiate** between normative and non-normative parts of WAI-ARIA and **justify** why that distinction matters for conformance.
7. **Explain** the purpose and impact of WAI-ARIA 1.2 on web accessibility
8. **Describe** the WAI-ARIA 1.2 model of roles, states, and properties
9. **Determine** when to use WAI-ARIA 1.2 versus standard HTML elements
10. **Apply** the five rules for using ARIA correctly
### ATAG 2.0
11. **Differentiate** between normative and non-normative parts of ATAG and **justify** why that distinction matters for conformance.
12. **Explain** how ATAG 2.0 applies to web content authoring tools
13. **Describe** the meaning and intent of the two main sections of ATAG 2.0 (Part A: Accessible user interface; Part B: Supporting accessible content production)
14. **Distinguish** between automated accessibility practices in authoring tools and practices requiring author/user input
15. **Evaluate** the power and limitations of automated accessibility authoring features
16. **Differentiate** between normative and non-normative information in ATAG 2.0
### EN 301 549
17. **Identify** the types of technologies addressed by EN 301 549
18. **Compare** and contrast the similarities and differences between WCAG and EN 301 549
19. **Explain** how WCAG is represented in EN 301 549
20. **Identify** requirements beyond WCAG that are relevant for compliance with the Web Accessibility Directive 2016/2102
21. **Interpret** the self-scoping (applicability) language used in EN 301 549
22. **Explain** the intent and scope of EN 301 549 requirements that extend beyond WCAG
I.B.
## I.B. Basic Knowledge of Programming
1. **Demonstrate** how JavaScript event handlers can be made device-independent (e.g., supporting both pointer and keyboard input).
2. **Explain** progressive enhancement and **outline** the implications of turning JavaScript off or using older browsers for accessibility.
3. **Identify** common pitfalls in dynamic content updates (e.g., partial page refreshes with AJAX) and **implement** focus management or live regions to keep screen reader users informed.
4. **Distinguish** between semantic HTML controls (e.g., `<button>`, `<a>`) and generic elements (e.g., `<div>`) in terms of built-in accessibility.
5. **Analyze** how focus order, event handling (onClick, onKeyDown, etc.), and ARIA states can either improve or harm the user experience for assistive technology.
### Imported Objectives (From objectives_export.md)
6. Analyze how JavaScript implementations can either improve or reduce accessibility and usability for people using assistive technologies.
7. Compare the accessibility implications of applying JavaScript event handlers (such as onclick) to semantic elements (e.g., `<a>` or `<button>`) versus non-semantic elements (e.g., `<div>`).
8. Determine appropriate focus management techniques for moving focus to newly revealed or dynamically generated content.
I.C.
## I.C. Create Interactive Controls/Widgets Based on Best Practices
1. **Construct** a custom widget (e.g., a modal dialog or accordion) using the WAI-ARIA Authoring Practices, ensuring correct roles, states, and properties.
2. **Demonstrate** correct keyboard interaction models (e.g., tab vs. arrow keys) for composite components such as menus, tabs, and disclosure widgets.
3. **Evaluate** existing custom controls for missing or incorrect ARIA markup, and **recommend** solutions to align them with best practices.
### Imported Objectives (From objectives_export.md)
4. Analyze accessibility of interactive components and ARIA-based widgets based on expected keyboard and screen reader behavior.
5. Analyze interactive components to ensure they support single-pointer alternatives for gesture-based interactions.
6. Apply established keyboard interaction conventions when testing ARIA-based custom widgets.
7. Apply established keyboard interaction models when implementing ARIA-based custom widgets, including the use of Tab to enter widgets and arrow keys to navigate within them.
8. Apply standard keyboard interaction models when designing and implementing ARIA-based custom widgets.
9. Evaluate accessibility of interactive components based on keyboard navigation and screen reader behavior.
10. Evaluate implementations of custom widgets to determine whether they follow established accessibility authoring practices.
11. Evaluate when native HTML controls should be used instead of custom ARIA widgets based on accessibility best practices and implementation complexity.
I.D.
## I.D. Using ARIA
1. **Explain** the five primary rules of ARIA usage (e.g., "use native HTML first," "do not change native semantics unless necessary").
2. **Implement** accessible names and descriptions using `aria-label`, `aria-labelledby`, and `aria-describedby`, and **justify** which approach is most appropriate in a given scenario.
3. **Demonstrate** correct focus management using `aria-activedescendant` or roving `tabindex` in interactive widgets.
4. **Analyze** how the accessibility tree is exposed to assistive technology and **verify** ARIA roles, states, and properties in different screen reader/browser combinations.
### Imported Objectives (From objectives_export.md)
5. Analyze accessibility implications of complex web applications and determine how ARIA roles, states, and properties can communicate interface changes to assistive technologies.
6. Analyze web interface patterns to determine when WAI-ARIA is appropriate.
7. Analyze widget implementations to determine whether appropriate WAI-ARIA roles, states, and properties are applied correctly.
8. Apply ARIA live region properties to announce dynamically added content without moving keyboard focus when appropriate.
9. Apply ARIA properties and states to communicate widget state and dynamic changes in user interfaces (e.g., checked, expanded).
10. Apply techniques for providing accessible names and descriptions to interactive controls and widgets.
11. Compare the accessibility benefits and limitations of native HTML controls and custom WAI-ARIA widgets.
12. Describe the semantic structure of ARIA roles, including required parent roles, child roles, and associated attributes.
13. Describe the WAI-ARIA roles, states, and properties model and how it communicates semantics to assistive technologies.
14. Determine appropriate use of ARIA live regions to notify assistive technologies of dynamic content updates.
15. Evaluate different techniques for notifying assistive technologies when dynamic content changes occur, including the use of ARIA live regions and related mechanisms.
16. Evaluate scenarios where the application role may be used and justify when it should be avoided due to its impact on assistive technology keyboard navigation.
17. Evaluate whether native HTML semantics or WAI-ARIA should be used in a given implementation scenario.
18. Explain how assigning an ARIA role overrides the native semantic role of an HTML element and the implications this has for accessibility APIs and assistive technologies.
19. Explain the five rules for using ARIA and their importance in accessible interface design.
20. Explain the purpose of WAI-ARIA and its role in improving accessibility for dynamic web content and custom interface components.
21. Explain the role of the accessibility tree in conveying semantic information from web content to assistive technologies.
22. Identify appropriate ARIA roles used to describe interactive widgets (e.g., menu, treeitem, slider, progressbar) and structural elements of a page (e.g., headings, regions, tables).
I.E.
## I.E. Accessibility-Supported Technologies
1. **Identify** how assistive technologies (e.g., screen readers, magnifiers, voice input) interact with browsers and what "accessibility-supported" means under WCAG.
2. **Assess** the compatibility of a chosen technology stack (front-end framework, JS library) with major screen reader/browser pairs and **recommend** fallback or polyfill strategies.
3. **Explain** how touch interaction changes with a screen reader turned on (e.g., iOS VoiceOver gestures) and **demonstrate** design patterns to support these gestures.
### Imported Objectives (From objectives_export.md)
4. Analyze accessibility issues to determine whether they result from design or implementation flaws versus limitations in browser or assistive technology support.
5. Distinguish between accessibility features that can be implemented automatically by authoring tools and those requiring author input.
6. Evaluate the capabilities and limitations of automated accessibility support within authoring tools.
7. Evaluate unexpected screen reader behavior to determine whether it results from accessibility issues in the web content, limitations in assistive technology support, or incorrect testing techniques.
8. Explain how ARIA can enhance assistive technology support for dynamic content and custom user interface components.
I.F.
## I.F. Standard Controls vs. Custom Controls
1. **Compare** native HTML controls' built-in accessibility features with custom (ARIA-based) components, highlighting pros and cons.
2. **Demonstrate** how to repurpose a non-semantic element into a fully accessible custom button or link using proper ARIA attributes, keyboard events, and visible focus.
3. **Recommend** standard HTML controls whenever possible and **justify** the business and user benefits of reducing custom code for accessibility.
I.G.
## I.G. Single-Page Applications (SPAs)
1. **Demonstrate** how to manage announcements of dynamic page updates (e.g., with `aria-live`) when navigation or content changes do not trigger a full page reload.
2. **Implement** focus changes appropriately when new views or dialogs appear, ensuring screen-reader and keyboard-only users can track SPA updates.
3. **Evaluate** the user experience of a single-page application with typical assistive technologies and **propose** solutions for any discovered gaps.
### Imported Objectives (From objectives_export.md)
4. Analyze dynamic content updates in SPAs to determine whether users should be notified when new content is loaded.
5. Evaluate touch interfaces to confirm that touch targets are large enough and sufficiently spaced.
6. Explain accessibility challenges associated with single-page applications (SPAs), including focus management, dynamic content updates, and assistive technology compatibility.
7. Test single-page application behaviors with screen readers to verify that asynchronous content updates are correctly announced and accessible.
8. Test whether focus indicators, labels, and instructions remain visible and usable at increased zoom levels or modified text spacing.
I.H.
## I.H. Strategies of Persons with Disabilities in Using Web Solutions
1. **Describe** key strategies that users with blindness, low vision, motor disabilities, auditory disabilities, and cognitive/learning disabilities employ to interact with web content.
2. **Analyze** design elements (e.g., headings, landmarks, color contrast) to determine their impact on diverse user groups' navigation and comprehension strategies.
3. **Propose** layout or structural revisions (e.g., skip links, consistent navigation) that accommodate multiple disability groups.
---
# Domain II: Identify Accessibility Issues in Web Solutions (40%)
### Imported Objectives (From objectives_export.md)
II.A.
## II.A. Interoperability and Compatibility Issues
1. **Identify** potential issues arising from specific browser–screen reader combinations (e.g., JAWS + Chrome vs. NVDA + Firefox).
2. **Explain** why certain ARIA roles or HTML5 elements might not be fully supported across older browsers, and how to mitigate these gaps.
3. **Evaluate** a website's accessibility across multiple devices (desktop, tablet, mobile) and assistive technologies.
### Imported Objectives (From objectives_export.md)
4. Analyze how accessibility support changes when assistive technologies are combined with different user agents.
5. Analyze how users with disabilities interact with web content using assistive technologies, adaptive strategies, and user agents.
6. Describe how assistive technologies interact with user agents, including browsers and applications.
7. Explain how web content, user agents (browsers and media players), assistive technologies, and authoring tools interact to provide an accessible web experience.
II.B.
## II.B. Identifying Guidelines and Principles Regarding Issues
1. **Map** discovered accessibility barriers to the appropriate WCAG success criterion (or EN 301 549 clause) and **distinguish** conformance failures from best-practice gaps.
2. **Apply** the WCAG-EM methodology to define scope, explore site content, select a representative sample, and evaluate conformance thoroughly.
3. **Explain** the concept of conformance levels (A, AA, AAA) and **defend** the rationale for choosing a specific level in a project or legal context.
4. **Describe** the limitations in WCAG (e.g., certain gaps for cognitive or motion-based issues) and **propose** best-practice enhancements.
### Imported Objectives (From objectives_export.md)
5. Analyze accessibility issues to determine whether they represent failures of WCAG Success Criteria or broader usability or accessibility concerns not explicitly covered by the specifications.
6. Analyze differences in how assistive technology users may interact with web content based on skill level, navigation strategies, and personal preferences.
7. Analyze dynamic content updates to determine when keyboard focus should be moved to newly loaded content.
8. Analyze examples of web content to determine whether they meet or fail specific WCAG success criteria.
9. Analyze the scope and intent of the requirements listed in Annex A, Table A.1 in EN 301 549 that go beyond WCAG.
10. Apply standard keyboard interaction patterns to test native HTML interactive elements.
11. Apply the WCAG Evaluation Methodology (WCAG-EM) to systematically evaluate the accessibility of web content.
12. Assess caption accuracy and completeness to ensure that automatic captioning errors have been corrected.
13. Assess form fields to ensure appropriate autocomplete attributes are implemented where relevant.
14. Classify WCAG 2.2 Success Criteria according to their conformance levels (A, AA, AAA).
15. Compare the accessibility requirements in EN 301 549 with those defined in WCAG.
16. Describe the purpose and scope of the two primary sections of ATAG 2.0.
17. Describe the relationship between WCAG principles, guidelines, and success criteria.
18. Differentiate between accessibility issues that can be detected by automated tools and those that require manual evaluation.
19. Differentiate between sufficient techniques, advisory techniques, and failures associated with WCAG success criteria.
20. Differentiate between the disciplines of accessibility and user experience (UX) design, including their goals, assumptions, and areas of overlap.
21. Distinguish between normative and non-normative information within accessibility specifications.
22. Explain factors that influence the selection of a target accessibility conformance level (e.g., legal requirements, organizational policies, or project goals).
23. Explain how ATAG 2.0 applies to web content authoring tools and development environments.
24. Explain how WCAG requirements are incorporated into EN 301 549.
25. Explain the intent and accessibility impact of each WCAG principle.
26. Explain WCAG conformance requirements and how they apply to evaluating web content.
27. Identify additional accessibility requirements in EN 301 549 that extend beyond WCAG.
28. Identify relevant accessibility requirements in specifications such as WCAG 2.2, WAI-ARIA, and ATAG when evaluating accessibility issues.
29. Identify the technologies and digital products addressed by EN 301 549.
30. Identify WCAG 2.2 Success Criteria and their associated conformance levels (A, AA, AAA).
31. Interpret the intent and requirements of ATAG principles, guidelines, and success criteria.
32. Interpret the requirements of WCAG success criteria and their implications for accessible design and development.
33. Summarize the major additions introduced in WCAG 2.1, particularly those addressing new input methods and improved support for low vision and cognitive disabilities.
II.C.
## II.C. Testing with Assistive Technologies
1. **Conduct** screen reader testing to confirm that name, role, value, and state changes of interactive elements are conveyed properly.
2. **Demonstrate** manual keyboard testing to detect missing focus indicators, incorrect tab order, or keyboard traps.
3. **Use** magnifier or high-contrast settings to **detect** any text or interface elements that become unusable or unreadable.
4. **Identify** common user needs for auditory disabilities (e.g., accurate captions, transcripts) and evaluate if they are met.
### Imported Objectives (From objectives_export.md)
5. Evaluate focus management, focus order, and visibility of focus indicators during keyboard navigation.
6. Evaluate form implementations based on expected screen reader interaction patterns.
7. Evaluate HTML markup to verify that semantic structure (e.g., headings, lists, tables, and landmarks) correctly conveys meaning to assistive technologies.
8. Evaluate keyboard operability, focus order, and link descriptions to ensure they support effective screen reader navigation.
9. Evaluate navigation structures, headings, and labels to determine whether they provide clear and consistent information architecture.
10. Evaluate responsive behavior to ensure content adapts to different viewport sizes without requiring two-dimensional scrolling.
11. Evaluate scenarios where it may be appropriate to supplement or override browser or assistive technology behavior to improve accessibility, while considering potential risks and compatibility impacts.
12. Evaluate the limitations of accessibility guidelines, principles, and techniques when assessing real-world accessibility issues.
13. Evaluate web content to determine whether text alternatives are provided for images, video, and other non-text content.
14. Evaluate web implementations to ensure accessibility solutions follow established web standards rather than relying on technology-specific quirks.
15. Test character-key shortcuts to ensure they can be disabled, remapped, or activated only when the relevant component has focus.
16. Test dynamic content updates to confirm that roles, names, values, and status messages are communicated to screen readers using appropriate ARIA attributes or live regions.
17. Test the reading order of web content to confirm that the programmatic order is meaningful and consistent with the intended visual presentation.
18. Test web interfaces to confirm that all functionality can be operated using a keyboard without keyboard traps.
19. Verify that error messages are programmatically associated with form fields and that clear instructions and suggestions for correction are provided.
20. Verify that page language, form errors, and component states are programmatically conveyed to assistive technologies.
II.D.
## II.D. Testing Tools for the Web
1. **Compare** the strengths and limitations of automated tools, browser-based linters, spider tools, and bookmarklets for accessibility testing.
2. **Use** at least one site-wide scanning tool and one browser-based developer tool (e.g., Axe, WAVE, Lighthouse) to **detect** markup or ARIA errors.
3. **Interpret** automated test results to confirm valid failures, eliminate false positives, and plan follow-up manual checks.
### Imported Objectives (From objectives_export.md)
4. Analyze accessibility issues identified by testing tools and determine appropriate follow-up manual testing strategies.
5. Analyze automated accessibility testing results to identify false positives, omissions, and issues requiring manual verification.
6. Analyze how accessibility testing tools can be applied at different stages of the web development lifecycle, including design, development, and testing.
7. Analyze how accessibility testing tools can be integrated at different stages of the web development lifecycle, including design, development, and testing.
8. Evaluate the strengths and limitations of automated accessibility testing tools.
9. Explain the purpose of Accessibility Conformance Testing (ACT) Rules and their role in standardizing automated accessibility testing.
10. Identify common categories of accessibility testing tools, including site-wide scanning tools, server-based analysis tools, unit and integration testing tools, browser developer tools, browser extensions, simulators, and guided manual testing tools.
11. Inspect HTML structure and accessibility attributes using browser developer tools to identify potential accessibility issues.
12. Inspect HTML structure and accessibility-related attributes using browser developer tools.
II.E.
## II.E. Accessibility Quality Assurance
1. **Explain** how accessibility can be integrated into agile vs. waterfall lifecycles, focusing on early detection of issues.
2. **Establish** a continuous testing process (automated + manual) that catches regressions after updates or new releases.
3. **Coordinate** with product owners, designers, and developers to incorporate accessibility checks into acceptance criteria and "definition of done."
### Imported Objectives (From objectives_export.md)
4. Analyze development workflows to determine how accessibility practices can be incorporated into ongoing quality assurance and regression testing processes.
5. Compare Agile and Waterfall project management methodologies and analyze how each approach incorporates accessibility quality assurance activities.
6. Explain how accessibility considerations should be integrated throughout the product development lifecycle, including concept, requirements, design, prototyping, development, quality assurance, user testing, support, and regression testing.
7. Explain how accessibility maturity models and assessment tools can be used to measure progress and support long-term accessibility sustainability.
II.F.
## II.F. Testing with Assistive Technologies (Extended)
1. **Demonstrate** usage of at least two popular screen reader/browser combinations (e.g., NVDA + Firefox, VoiceOver + Safari) to confirm consistent user experience.
2. **Verify** that dynamically updated or hidden elements are properly announced or hidden from screen readers.
3. **Assess** whether alternative input methods (switch control, voice input) can navigate and operate interactive elements effectively.
### Imported Objectives (From objectives_export.md)
4. Evaluate whether interactive elements are implemented using native controls or appropriate ARIA semantics to support voice control and alternative input devices.
5. Identify issues for users who use keyboard or alternative input devices.
II.G.
## II.G. Testing for End-User Impact (Low Vision, Cognitive, Mobile/Touch)
1. **Perform** usability walk-throughs with simulated low-vision settings (zoom, high contrast) to find layout or text-flow issues.
2. **Assess** mobile interaction (touch gestures, orientation changes) to **ensure** elements remain accessible and do not require two-dimensional scrolling.
3. **Identify** potential cognitive barriers (e.g., complex language or form instructions) and **recommend** simpler language or multi-step guidance.
### Imported Objectives (From objectives_export.md)
4. Evaluate motion-based interactions to ensure they can be disabled and replaced with accessible controls.
5. Evaluate multimedia content to verify that captions are provided for video and transcripts are available for audio-only content.
6. Evaluate the impact of contrast enhancement modes (such as Windows High Contrast Mode) on the presentation and usability of web interfaces.
7. Evaluate time limits, moving content, and automatically playing media to determine whether users can control or disable them.
8. Explain how touch-based interactions change when screen readers are enabled on mobile devices.
9. Identify accessibility issues related to sensory-dependent instructions, automatically playing audio, or moving content that may interfere with screen reader use.
10. Test device orientation support to ensure content and functionality are available in both portrait and landscape orientations.
11. Test mobile interfaces to confirm that all functionality available on desktop viewports is also accessible on smaller touch screens.
12. Test web interfaces for sufficient text and non-text contrast.
13. Understand the principles of color contrast requirements in web accessibility and evaluate when and how they apply to ensure text and visual elements are perceivable to users with visual impairments.
14. Verify that gesture-based interactions provide accessible single-pointer alternatives.
15. Verify that motion-based or device-motion interactions provide accessible alternative controls.
16. Verify that text can be resized up to 200% without loss of functionality or content.
II.H.
## II.H. Testing Tools for the Web (Revisited)
1. **Demonstrate** how to use color-contrast analyzers, focus inspectors, or code validators to confirm partial compliance with WCAG criteria.
2. **Explain** how ACT Rules can guide consistent test procedures across multiple tools and testers.
---
# Domain III: Remediating Issues in Web Solutions (20%)
III.A.
## III.A. Level of Severity and Prioritization of Issues
1. **Categorize** accessibility issues based on severity (blockers vs. minor nuisances) and **formulate** a remediation timeline that balances user impact and resource constraints.
2. **Justify** which issues must be addressed first by assessing legal risk, user impact, and overall usability.
3. **Demonstrate** how to communicate high-impact barriers (e.g., no keyboard support, missing alt text on key images) to stakeholders and developers.
### Imported Objectives (From objectives_export.md)
4. Analyze accessibility issues to determine their severity based on user impact, legal risk, and implementation effort.
5. Assess the severity and user impact of accessibility barriers, recognizing that some issues create greater barriers than others.
6. Evaluate the importance and urgency of dynamically loaded content to determine the most appropriate notification strategy for assistive technology users.
7. Prioritize accessibility remediation tasks using cost–benefit considerations and the potential impact on users with disabilities.
III.B.
## III.B. Recommending Strategies and/or Techniques for Fixing Issues
1. **Propose** ARIA-based or native HTML solutions for each conformance failure, **explaining** why a given fix is both accessible and feasible.
2. **Distinguish** between "quick fixes" that resolve localized errors and "redesign" approaches that address deeper structural problems.
3. **Collaborate** with design and development teams to **implement** new UI patterns or code libraries that systematically eliminate repeated accessibility faults.
### Imported Objectives (From objectives_export.md)
4. Analyze results from automated and manual testing tools to determine appropriate follow-up testing or remediation steps.
5. Assess remediation strategies to determine whether an ideal solution or a “good enough” solution is appropriate given project constraints, target users, and available resources.
6. Communicate remediation strategies, including the purpose, approach, and expected outcomes, to relevant stakeholders.
7. Communicate the purpose, approach, and expected outcomes of accessibility remediation strategies to relevant stakeholders.
8. Differentiate between targeted accessibility fixes and broader redesign approaches when addressing accessibility barriers.
9. Evaluate remediation options to determine whether a targeted fix or a broader redesign is the most appropriate solution.
10. Evaluate remediation strategies to determine the most practical and widely applicable solution for a given accessibility issue.
11. Evaluate the benefits of integrating accessibility during design and development compared to addressing accessibility through post-development remediation.
12. Identify appropriate stakeholders and engage them in planning and implementing accessibility remediation efforts.
13. Identify key stakeholders involved in accessibility remediation and engage them in planning and implementing solutions.
14. Incorporate feedback from users with disabilities to validate and improve remediation approaches.
15. Incorporate feedback from users with disabilities to validate and refine remediation strategies.
16. Recommend practical remediation techniques that improve accessibility while minimizing disruption to existing systems.
17. Recommend practical techniques that improve accessibility while minimizing disruption to existing systems.
III.C.
## III.C. Integrate Accessibility into the Procurement Process
1. **Evaluate** vendor Accessibility Conformance Reports (VPAT/ACR) to determine product compatibility with organizational accessibility standards.
2. **Recommend** contract language that mandates the vendor to fix accessibility defects within specified timeframes and supply updated VPATs.
3. **Develop** a procurement checklist incorporating EN 301 549 or WCAG references to ensure new products and services meet accessibility requirements.
4. **Implement** a vendor management process that includes accessibility roadmap reviews, defect remediation, and ongoing conformance monitoring.
### Imported Objectives (From objectives_export.md)
5. Analyze compatibility issues that occur across different combinations of assistive technologies, browsers, and operating systems.
6. Assess the feasibility of proposed remediation solutions across different project contexts and technical environments.
7. Compare how assistive technologies behave across different platforms, devices, and operating systems.
8. Compare interaction methods used by assistive technologies across platforms, including keyboard-based navigation on desktop and gesture-based navigation on mobile devices.
9. Describe how device-independent event handlers support accessibility across keyboard, mouse, touch, and assistive technology interactions.
10. Differentiate between types of Accessibility Conformance Reports (ACRs) and interpret the accessibility information they provide.
11. Evaluate accessibility claims and documented conformance statements within procurement documentation.
12. Evaluate design decisions related to selecting technologies that support accessibility across platforms and assistive technologies.
13. Evaluate web interfaces for interoperability across browsers, platforms, and assistive technologies (e.g., JAWS, NVDA, VoiceOver, Chrome, Safari).
14. Explain how accessibility requirements can be incorporated into organizational procurement processes.
15. Explain the role of accessibility experts in evaluating vendors and advising on accessibility requirements during procurement.
16. Identify accessibility risks and issues raised during procurement evaluations.
17. Recommend mitigation strategies to address accessibility gaps identified during the procurement process.
18. Test interactive components for accessibility across multiple browsers, platforms, and assistive technologies.
