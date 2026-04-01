# Web Accessibility Specialist (WAS) Learning Objectives
## Objectives 128-332

## Domain Two: Identify Accessibility Issues in Web Solutions (40%)

### Domain Two A: Interoperability and Compatibility Issues

128. Identify the needs of users with different types of disabilities as outlined in EN 301 549's Functional Performance statements
129. Explain how keyboard support serves as a requirement for multiple types of assistive technologies
130. List the most commonly used screen readers (JAWS, NVDA, VoiceOver)
131. Specify recommended browser and screen reader combinations for Windows, macOS, iOS, and Android platforms
132. Identify issues for methods, technologies, and strategies used by people with disabilities

### Domain Two B: Identifying Guidelines and Principles Regarding Issues

133. Distinguish between normative and non-normative content in WCAG documentation
134. Identify which Success Criteria apply to Level A, AA, and AAA conformance levels
135. List the five WCAG conformance requirements that content must meet to achieve conformance
136. Explain the difference between WCAG 2.0, 2.1, and 2.2 Success Criteria
137. Describe the additional requirements in EN 301 549 beyond WCAG Success Criteria (38 additional requirements)
138. Apply the WCAG-EM methodology's five main steps for website evaluation
139. Distinguish between true accessibility failures and poor design practices not covered in specifications
140. Explain the pass/fail conformance model and its implications for accessibility testing
141. Identify the four Success Criteria required for non-interference conformance
142. Map accessibility issues to specific WCAG Success Criteria accurately
143. Recognize the limitations of WCAG 2.2 (pseudomotion, color blindness, cognitive load, etc.)

### Domain Two C: Testing with Assistive Technologies (Screen Reader Users)

144. Verify that alternatives exist for images and video content
145. Evaluate whether semantic markup conveys meaning appropriately (headings, lists, tables, paragraphs)
146. Test that content order presented to assistive technology is meaningful
147. Confirm that instructions are not based on sensory characteristics alone
148. Verify that automatically playing audio can be turned off
149. Test that scrolling or moving content can be stopped by the user
150. Evaluate page titles for descriptive topic or purpose
151. Verify methods exist to bypass repeated content (skip links, landmarks, section headings)
152. Test that all functionality is operable via keyboard with no keyboard trap
153. Evaluate that focus order is logical, intuitive, and predictable
154. Verify that link text is descriptive or determinable with context
155. Test that the correct page language is set for proper screen reader pronunciation
156. Verify error messages are programmatically identifiable and described in text
157. Test that role, name, and value of interactive components are available and updated correctly
158. Evaluate that dynamic status messages are conveyed using live regions

### Domain Two C: Testing with Assistive Technologies (Keyboard/Alternative Input Users)

159. Verify all functionality is operable via keyboard with no keyboard trap
160. Test that methods exist to bypass repeated content
161. Evaluate that focus order is logical, intuitive, and predictable
162. Verify that focus indicator is easily visible
163. Test that multipoint or path-based gestures can be operated with single pointer
164. Verify that only up-events execute functions or users can reverse/undo
165. Test that device motion functionality has alternative UI controls
166. Verify motion activation can be disabled to prevent accidental activation
167. Test that interactive elements use native controls or proper ARIA markup
168. Verify character key shortcuts can be turned off, remapped, or are only active on focus
169. Test that audio can be turned off for voice control users
170. Verify programmatic labels match visual labels

### Domain Two C: Testing with Assistive Technologies (Auditory Disabilities)

171. Verify videos have accurate captions
172. Test that automatic captioning errors are corrected
173. Verify transcripts are provided for audio-only content

### Domain Two C: Testing with Assistive Technologies (Low Vision Users)

174. Verify no restriction to single display orientation (portrait or landscape)
175. Test that color alone is not used to convey information
176. Verify sufficient contrast of text elements
177. Test sufficient contrast of non-text elements (icons, input field borders)
178. Verify text can be resized to 200%
179. Test for no loss of functionality when zooming to 200%
180. Verify use of real text instead of images of text
181. Test that no two-dimensional scrolling is necessary
182. Verify no loss of content or functionality when users change text spacing
183. Test that content appearing on hover/focus can be dismissed, doesn't auto-close, and can be hovered over

### Domain Two C: Testing with Assistive Technologies (Cognitive/Learning Disabilities)

184. Verify input fields have appropriate autocomplete attributes
185. Test that automatically playing audio can be turned off
186. Verify session timeouts can be turned off or adjusted
187. Test that page titles describe topic or purpose
188. Verify link text is descriptive or determinable with context
189. Test that multiple ways to locate pages are available
190. Verify headings and labels are descriptive
191. Test that no UI component causes unexpected context change on focus
192. Verify no UI component causes unexpected context change when setting is changed
193. Test that navigation mechanisms are positioned consistently
194. Verify components with same functionality are identified consistently
195. Test that error messages are identifiable and described
196. Verify descriptive labels or instructions for user input elements are available
197. Test that error suggestions are provided
198. Verify error prevention mechanisms exist for legal and financial data

### Domain Two C: Testing with Assistive Technologies (Touch Users)

199. Verify large touch target sizes
200. Test adequate spacing between touch targets
201. Verify no restriction to single display orientation
202. Test that multipoint or path-based gestures have single pointer alternatives
203. Verify device motion functionality has alternative UI controls
204. Test that motion activation can be disabled
205. Verify all content/functionality available at desktop widths is accessible on small touch screens

### Domain Two D: Testing Tools for the Web

206. Explain the purpose and limitations of ACT Rules
207. Identify that ACT Rules check for failures but passing does not guarantee full conformance
208. Distinguish between accessibility issues found by automated tools versus those requiring manual testing
209. List types of software tools available (site-wide scanning, server-based analysis, unit testing, integration testing, browser developer tools, browser add-ons, simulators, guided manual testing)
210. Recognize that automated tools can include false positives
211. Identify that automated tools cannot determine conformance alone
212. Use browser's built-in Development Tools to inspect source code
213. Navigate ARIA custom widgets using keyboard and screen readers
214. Apply standard keystrokes for interaction with interactive elements in native HTML
215. Interpret results of automatic testing and identify false positives and omissions

### Domain Two E: Accessibility Quality Assurance

216. Differentiate between Agile and Waterfall project management methodologies regarding accessibility quality assurance
217. Explain the benefits of designing with accessibility in mind versus remediation
218. Distinguish between accessibility and user experience design disciplines
219. Identify how accessibility integrates into the entire product life cycle (concept, requirements, design, prototyping, development, QA, user testing, support, regression testing)
220. Describe each team member's role in delivering accessible products
221. Apply the Plan-Create-Test cycle for accessibility integration
222. Implement accessibility in information architecture and user experience
223. Determine budget and resources for accessibility implementation
224. Document accessibility goals and define conformance in "Definition of done"
225. Ensure team members have access to accessibility expertise and training

### Domain Two F: Testing with Assistive Technologies (Detailed)

226. Identify recommended screen reader and browser combinations
227. Navigate content via landmarks and headings using screen readers
228. Use screen reader forms mode and application mode appropriately
229. Understand different screen reader modes (browse mode, forms mode, application mode, VoiceOver rotor, TalkBack menu)
230. Apply standard keystrokes for native HTML interactive elements
231. Apply conventions for keyboard interaction within ARIA widgets
232. Recognize limitations of personal assistive technology knowledge
233. Distinguish between screen reader bugs and actual accessibility issues
234. Test ARIA constructs and components with screen readers
235. Verify state changes are announced to screen reader users
236. Test that hidden content is appropriately hidden both visually and programmatically
237. Identify CSS issues affecting assistive technology users

### Domain Two F: Manual Testing - Keyboard

238. Verify all functionality is operable via keyboard
239. Test for keyboard traps
240. Verify methods to bypass repeated content exist
241. Test that focus order is logical, intuitive, and predictable
242. Verify focus movement within components/widgets is as expected
243. Test that focus indicator is visible
244. Verify visual labels match programmatic labels

### Domain Two F: Manual Testing - Content

245. Verify headings, lists, and structural elements are marked up correctly
246. Test that titles, headings, and form labels are descriptive
247. Verify links are descriptive in context
248. Test that language changes are marked up accordingly
249. Verify no loss of functionality when zooming to 200%
250. Test that text can be resized to 200%
251. Verify no loss of content/functionality when text spacing is changed
252. Test that text alternatives for images are accurate and meaningful
253. Verify alternatives for video (captions, audio description) and audio are provided and accurate
254. Test that users can stop animation or it stops automatically after 5 seconds
255. Verify no content flashes above threshold
256. Test sufficient contrast (including text on gradients or images)
257. Verify color is not used as sole means to convey information
258. Test that navigation mechanisms occur in same order across pages
259. Verify components with same functionality are identified consistently

### Domain Two G: Testing for End-User Impact

260. Explain the value of user testing with people with various disabilities
261. Assess consequences of different types of accessibility flaws
262. Distinguish between design usability, accessibility, and conformance to specifications
263. Recognize that WCAG conformance is minimum requirement, not comprehensive usability guarantee
264. Identify accessibility techniques not yet documented in WCAG
265. Explain how content can be accessible but not usable for end-users
266. Recommend supplemental guidance beyond WCAG requirements for better usability
267. Involve people with disabilities in requirements and early development stages
268. Conduct task-based usability tests with native assistive technology users
269. Recognize diversity among users with disabilities affects user experience

### Domain Two H: Testing Tools for the Web (Comprehensive)

270. Use guided manual testing tools based on heuristics (Accessibility Insights, ARC Platform, Axe Auditor, JAWS Inspect)
271. Use browser developer tools and add-ons for accessibility testing
272. Use accessibility API viewers (Accessibility Viewer for Windows, XCode Accessibility Inspector for MacOS)
273. Use simulators for colorblindness and low vision testing (Colour Oracle, No Coffee vision simulator)
274. Use single-purpose tools (Headings Map, PEAT, Contrast Checker, Colour Contrast Analyser)
275. Apply ACT Rules in testing methodologies
276. Interpret automated testing results and identify limitations
277. Combine automated and manual testing approaches effectively
278. Select appropriate testing tools for different stages of web development process

## Domain Three: Remediating Issues in Web Solutions (20%)

### Domain Three A: Level of Severity and Prioritization of Issues

279. Prioritize issues based on impact (high, medium, low) on users with disabilities
280. Identify low-effort repairs that can be addressed quickly
281. Prioritize repeated issues that occur across templates, component libraries, or design systems
282. Focus remediation on key content, high-traffic pages, and essential tasks
283. Assess cost-benefit of remediation efforts
284. Consider impact on interface when prioritizing remediation
285. Evaluate legal risk of identified issues
286. Determine if issues have high impact that prevents task completion (CAPTCHA without alternative, keyboard-inaccessible controls, hidden content)
287. Distinguish between critical issues and medium-impact issues
288. Apply EN 301 549 Annex B to determine impact on different user groups

### Domain Three B: Recommending Strategies and Techniques for Fixing Issues

289. Distinguish between ideal/best solution and "good enough" solution based on project constraints
290. Explain the role of end users in assessing and validating remediation approaches
291. Differentiate between fixing particular issues and complete page redesign
292. Assess feasibility of particular solutions in different contexts
293. Provide practical and simple hints for better web accessibility
294. Communicate purpose, approach, and strategy for remediation clearly
295. Engage appropriate stakeholders in implementation recommendations
296. Use maturity models and tools to illustrate progress and sustainability
297. Distinguish between WCAG conformance failures and optional best practices
298. Recognize that multiple techniques can satisfy a Success Criterion
299. Refer to WCAG Understanding texts, Techniques, and ARIA Authoring Practices Guidelines

### Domain Three B: Fixing vs. Redesign Decisions

300. Evaluate severity and scope of defects to determine remediation vs. rewrite
301. Assess code complexity and maintainability when deciding on approach
302. Prioritize user experience in remediation decisions
303. Consider available resources (time, budget, expertise) in approach selection
304. Plan for future-proofing through comprehensive rewrites when appropriate
305. Apply hybrid approaches (immediate remediation for critical issues, long-term rewrite planning)

### Domain Three C: Integrate Accessibility into the Procurement Process

306. Incorporate accessibility into procurement process from the beginning
307. Provide guidance on good governance practices for procurement
308. Advise on ICT procurement standards such as EN 301 549
309. Develop suitable questions for tender documents and RFPs
310. Evaluate tender responses, ACRs, and VPATs
311. Conduct product testing during procurement
312. Suggest contract wording regarding accessibility
313. Manage vendors including defect remediation and accessibility roadmaps
314. Audit existing systems as part of procurement process
315. Create Accessibility Conformance Reports (ACRs)
316. Respond to tender questions regarding accessibility

### Domain Three C: Accessibility Conformance Reports

317. Explain the purpose of ACRs and VPATs
318. Distinguish between VPAT formats (2.4 Rev 508, 2.4 Rev EU, 2.4 Rev WCAG, 2.4 INT)
319. Interpret ACR conformance levels (Supports, Partially Supports, Does Not Support, Not Applicable)
320. Evaluate quality of vendor-provided ACRs
321. Identify when independent accessibility professionals should create ACRs
322. Use ACR information to guide product reviews

### Domain Three C: Mitigating Accessibility Defects

323. Obtain roadmaps for addressing known accessibility issues from vendors
324. Include binding accessibility commitments in contracts
325. Implement alternative access plans for users when defects exist
326. Monitor vendor performance in defect management
327. Consider accessibility performance during contract negotiations and renewals
328. Apply accessible procurement maturity models (PDAA, W3C maturity model)
329. Use maturity models to assess current accessibility practices
330. Measure progress over time using maturity model frameworks
331. Ensure accessibility is systematically considered in purchasing decisions
332. Foster long-term, sustainable accessibility improvements across supply chain

---

## Document Information

**Source:** Web Accessibility Specialist Body of Knowledge 2024  
**Organization:** International Association of Accessibility Professionals (IAAP)  
**Domains Covered:** Domain Two (Identify Issues) and Domain Three (Remediate Issues)  
**Total Objectives:** 205 (numbered 128-332)

## Notes

- These learning objectives are measurable and action-oriented
- They are organized according to the WAS Body of Knowledge structure
- Objectives cover 60% of the WAS certification exam content (Domains 2 and 3)
- Each objective can be assessed through testing, demonstration, or evaluation activities
