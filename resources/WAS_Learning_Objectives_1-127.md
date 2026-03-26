# Web Accessibility Specialist Learning Objectives

## Domain One: Creating Accessible Web Solutions (40%)

---

### Domain One A: Guidelines, Principles and Techniques for Meeting Success Criteria

#### WCAG 2.2

1. Identify and explain the four POUR principles (Perceivable, Operable, Understandable, Robust) and their relationship to guidelines and success criteria

2. Distinguish between the three conformance levels (A, AA, AAA) and identify the conformance level of each WCAG 2.2 success criterion

3. Differentiate between normative and non-normative information in WCAG 2.2

4. Explain the intent, requirements, and impact of each WCAG 2.2 principle, guideline, and success criterion

5. Identify and apply Sufficient Techniques, Failure Techniques, and Advisory Techniques for each success criterion

6. Describe the three types of techniques (Sufficient, Failure, Advisory) and the W3C vetting process for techniques

7. Explain the additive approach of WCAG versions and how WCAG 2.2 conforms to earlier versions

#### WAI-ARIA 1.2

8. Explain the purpose and impact of WAI-ARIA 1.2 on web accessibility

9. Describe the WAI-ARIA 1.2 model of roles, states, and properties

10. Determine when to use WAI-ARIA 1.2 versus standard HTML elements

11. Apply the five rules for using ARIA correctly

#### ATAG 2.0

12. Explain how ATAG 2.0 applies to web content authoring tools

13. Describe the meaning and intent of the two main sections of ATAG 2.0 (Part A: Accessible user interface; Part B: Supporting accessible content production)

14. Distinguish between automated accessibility practices in authoring tools and practices requiring author/user input

15. Evaluate the power and limitations of automated accessibility authoring features

16. Differentiate between normative and non-normative information in ATAG 2.0

#### EN 301 549

17. Identify the types of technologies addressed by EN 301 549

18. Compare and contrast the similarities and differences between WCAG and EN 301 549

19. Explain how WCAG is represented in EN 301 549

20. Identify requirements beyond WCAG that are relevant for compliance with the Web Accessibility Directive 2016/2102

21. Interpret the self-scoping (applicability) language used in EN 301 549

22. Explain the intent and scope of EN 301 549 requirements that extend beyond WCAG

---

### Domain One B: Basic Knowledge of Programming

#### JavaScript and Accessibility

23. Explain the concept of progressive enhancement and its importance for accessibility

24. Analyze how JavaScript can improve or damage accessibility depending on its use

25. Describe the impact of device-independent event handlers on accessibility

26. Compare the accessibility implications of applying onClick() to native semantic elements versus non-semantic elements

27. Explain user expectations regarding focus movement in web applications

28. Demonstrate when and how to send focus to new content using JavaScript

29. Identify methods to notify screen readers that new content has been added dynamically (e.g., ARIA live regions, focus management)

#### Managing Focus and State

30. Implement proper focus management when JavaScript changes visual focus

31. Apply roving tabindex technique for managing focus within composite widgets

32. Apply aria-activedescendant property for managing focus within composite widgets

33. Use JavaScript to toggle ARIA state attributes to convey component state to assistive technologies

34. Configure ARIA live regions correctly so content is reliably announced across platforms

---

### Domain One C: Create Interactive Controls/Widgets Based on Accessibility Best Practices

35. Apply the 5 rules for using ARIA when creating custom widgets

36. Explain the importance of coding to standards rather than to quirks of specific technologies

37. Identify semantic structure requirements for ARIA roles, including required parent/child roles and required attributes

38. Implement techniques for providing accessible names and descriptions to custom widgets

39. Apply authoring practices for custom widgets including semantic structure and keyboard behavior

40. Implement keyboard interaction models for ARIA custom widgets, including general patterns and widget-specific patterns

41. Test web designs for accessibility across various platforms, browsers, and assistive technologies

42. Determine when an inaccessible outcome results from design flaws versus poor technology support

43. Evaluate when it's appropriate to implement workarounds for browser or assistive technology bugs

---

### Domain One D: Using ARIA

#### Accessible Names and Descriptions

44. Define accessible name and accessible description and explain how they differ

45. Explain the Accessible Name and Description Computation algorithm

46. Identify sources that contribute to accessible names (e.g., aria-label, aria-labelledby, alt text, label elements)

47. Apply appropriate techniques to provide accessible names and descriptions to elements

#### ARIA Authoring Practice Guide

48. Navigate and utilize the ARIA Authoring Practice Guide (APG) to implement accessible custom widgets

49. Identify the limitations of the APG sample code (e.g., lack of comprehensive compatibility testing)

50. Apply keyboard interaction conventions from the APG to custom widgets

51. Distinguish between the "Patterns" and "Practices" sections of the APG

#### The Accessibility Tree

52. Explain how the Document Object Model (DOM) relates to the Accessibility Tree

53. Describe how the Accessibility API provides information to assistive technologies

54. Identify the five types of information provided by ARIA attributes (role, state, name, description, relationship)

55. Explain how semantic HTML elements have implicit ARIA semantics

56. Analyze how DOM content affects information available in the Accessibility Tree

#### ARIA Roles, States, and Properties

57. Categorize ARIA roles (Abstract, Widget, Document Structure, Landmark, Live Region, Window)

58. Distinguish between ARIA states and properties and explain when values typically change

59. Apply appropriate ARIA roles to non-semantic elements to convey meaning

60. Use ARIA states and properties to provide information about element status to assistive technologies

61. Explain how ARIA attributes are mapped to the operating system's accessibility API

---

### Domain One E: Accessibility-Supported Technologies

62. Define "accessibility-supported" technology according to WCAG conformance requirements

63. Explain why new technologies may not be immediately accessibility-supported

64. Identify when it's appropriate to implement workarounds, compromises, or polyfills for assistive technology bugs

65. Describe the risks associated with using polyfills for accessibility

66. Compare screen reader behavior and support across different platforms and devices

67. Explain how touch interactions change when screen readers are active (e.g., gesture-based navigation on mobile)

68. Analyze the role of ARIA in enhancing assistive technology support for dynamic content

---

### Domain One F: Standard Controls vs. Custom Controls

69. Explain the advantages of using standard HTML controls over custom controls

70. Identify situations when custom controls are necessary or appropriate

71. Apply proper ARIA roles, states, and properties when implementing custom controls

72. Implement keyboard interaction models for custom ARIA widgets

73. Compare the built-in accessibility features of native HTML elements to custom implementations

74. Evaluate when a custom role overrides native semantics and understand the implications

75. Apply keyboard conventions (tab, arrow keys, enter, space) appropriately for custom widgets

76. Explain when to use role="application" and why it should be used sparingly

---

### Domain One G: Single Page Applications

77. Identify accessibility challenges unique to single-page applications (SPAs)

78. Implement appropriate notification methods when AJAX content loads as a result of user action

79. Determine when users need to be notified about passively loaded AJAX content

80. Apply techniques to notify screen readers of new content (e.g., focus management, aria-live, page title updates)

81. Update page titles dynamically using JavaScript (document.title) in SPAs

82. Evaluate the importance and urgency of dynamically loaded content to determine notification strategy

---

### Domain One H: Strategies of Persons with Disabilities in Using Web Solutions

#### General Concepts

83. Define and distinguish between "assistive technology" and "adaptive strategies"

84. List different types of assistive technologies and adaptive strategies used by people with disabilities

85. Identify accessibility needs associated with different types of disabilities

86. Analyze how design decisions impact accessibility for people with various disabilities

#### Users Without Vision (Blind Users)

87. Explain how screen readers function and convert content to speech or braille

88. Describe common navigation strategies used by screen reader users (e.g., headings, landmarks, element lists)

89. Compare screen reader modes (browse/read mode, forms mode, application mode)

90. Explain how the interaction model differs for blind touchscreen users versus sighted touchscreen users

91. Identify how content reading order follows DOM order in screen readers

92. Explain why focus order must be logical and intuitive for screen reader users

93. Describe how screen readers use the Accessibility API to retrieve information

94. Identify most common screen readers and recommended browser combinations

#### Users with Low Vision

95. Describe strategies used by people with low vision (text enlargement, zoom, color changes, magnification)

96. Explain how magnification software works and its capabilities

97. Describe challenges faced by magnification users (orientation, focus tracking)

98. Explain how users with low vision often combine magnification with screen reading

99. Identify built-in magnification features across different platforms

100. Explain the importance of visible focus indicators for users with low vision

#### Users with Limited Reading Capacities

101. Identify groups of users with reading difficulties (ADHD, dyslexia, Irlen syndrome, memory loss)

102. Describe assistive technologies used by people with reading difficulties (text-to-speech, reading software)

103. Explain how text-to-speech software differs from full screen readers

104. List browser and operating system settings that support users with reading difficulties

105. Identify font and text presentation best practices for readability

106. Explain the importance of semantic markup and structured content for this user group

#### Users with Cognitive Disabilities

107. Describe the diverse range of cognitive disabilities and their impact on web use

108. Explain accessibility strategies for users with cognitive disabilities

109. Identify the importance of plain language, simple layout, and predictable design

110. Describe how users with cognitive disabilities may use assistive technologies (screen readers, magnification, focus tools)

111. Explain the benefits of providing content in multiple formats (text, images, audio)

112. Analyze how consistent web design supports users with cognitive disabilities

#### Users with Motor Disabilities

113. Identify the range of motor disabilities and their impact on computer use

114. Describe input methods used by people with motor disabilities (keyboard, switches, voice, eye-tracking)

115. Explain keyboard navigation strategies and why sequential navigation can be tedious

116. Describe the importance of visible focus indicators for keyboard users

117. Compare keyboard-only navigation to screen reader navigation

118. Explain how speech recognition software works for navigation and interaction

119. Describe the MouseGrid technique for users who cannot identify specific clickable elements

120. Identify built-in and third-party assistive technologies for users with motor disabilities (Dragon, switch controls, eye-tracking)

121. Explain the importance of large click targets and clear visual indicators for pointer users

122. Describe how voice recognition commands are often based on keyboard operations

---

## Cross-Domain Integration Objectives

123. Integrate knowledge from multiple domains to create comprehensive accessible web solutions

124. Evaluate websites and applications for conformance to WCAG 2.2 Level AA

125. Conduct accessibility testing using multiple assistive technologies and methods

126. Document accessibility issues and provide remediation recommendations

127. Apply user-centered design principles that consider diverse abilities and assistive technology users

---

## About This Document

This document contains measurable learning objectives for the Web Accessibility Specialist (WAS) certification, based on Domain One: Creating Accessible Web Solutions (40% of exam content). These objectives are organized according to the WAS Body of Knowledge structure and cover:

- WCAG 2.2, WAI-ARIA 1.2, ATAG 2.0, and EN 301 549 guidelines
- JavaScript programming concepts for accessibility
- Creating accessible interactive controls and widgets
- Proper use of ARIA roles, states, and properties
- Accessibility-supported technologies
- Standard vs. custom controls
- Single page application accessibility
- User strategies across different disability types

**Source:** IAAP Web Accessibility Specialist Body of Knowledge 2024
