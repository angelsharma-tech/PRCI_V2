# Test Cases: PRCI v2.0

## Overview

This document defines test scenarios for evaluating PRCI v2.0's system behavior and reliability. Each test case includes input description, expected system behavior, and clear pass/fail criteria for academic support functionality.

## Test Case Framework

### Test Structure

**Input Description**
- Clear description of academic situation or scenario
- Specific text input for system processing
- Context and background information for test scenario
- Expected user type and academic context

**Expected System Behavior**
- Appropriate detection results and risk assessment
- Expected intervention type and content
- System response format and structure
- Boundary compliance and ethical considerations

**Pass/Fail Criteria**
- Clear criteria for successful system behavior
- Specific requirements for system response accuracy
- Boundary compliance and ethical standard adherence
- Reliability and consistency requirements

## Test Case 1: Low-Risk Academic Stress

### Input Description

**Scenario**: Student experiencing mild academic stress with manageable workload
**Input Text**: "I have a few assignments due next week but I feel like I can handle them. Just need to stay focused and manage my time well."
**Context**: Regular academic workload with moderate stress levels
**User Type**: Typical university student with good time management skills

### Expected System Behavior

**Detection Results**
- Emotional Signal: Low to moderate stress indicators
- Root Cause: Time management optimization
- Confidence: High (appropriate academic context)

**Risk Assessment**
- Risk Level: LOW
- Risk Factors: Minimal procrastination indicators
- Academic Impact: Low risk to academic performance

**Intervention Response**
- Type: Motivational or encouragement focused
- Content: Positive reinforcement and productivity tips
- Tone: Supportive and encouraging
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System correctly identifies low-risk academic situation
- Intervention is motivational and non-directive
- Response maintains academic support boundaries
- System provides appropriate encouragement without clinical language

**Fail Criteria**
- System overestimates risk level (MEDIUM or HIGH)
- Intervention includes clinical or therapeutic language
- System provides inappropriate medical or psychological advice
- Response violates ethical boundaries or professional standards

## Test Case 2: Medium Academic Overload

### Input Description

**Scenario**: Student experiencing moderate academic overload with multiple deadlines
**Input Text**: "I have three major assignments due this week and I'm feeling overwhelmed. I keep procrastinating because there's too much to do and I don't know where to start."
**Context**: High academic workload with time pressure and stress
**User Type**: University student facing typical midterm or final exam stress

### Expected System Behavior

**Detection Results**
- Emotional Signal: Moderate to high stress indicators
- Root Cause: Task overload and overwhelm
- Confidence: High (clear academic context)

**Risk Assessment**
- Risk Level: MEDIUM
- Risk Factors: Task overload, time pressure, procrastination indicators
- Academic Impact: Moderate risk to academic performance

**Intervention Response**
- Type: Task breakdown and time management focused
- Content: Practical strategies for managing multiple deadlines
- Tone: Supportive and action-oriented
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System correctly identifies medium-risk academic situation
- Intervention focuses on task breakdown and time management
- Response provides practical, actionable academic strategies
- System maintains appropriate boundaries and non-clinical framing

**Fail Criteria**
- System misidentifies risk level (LOW or HIGH)
- Intervention includes inappropriate clinical or medical advice
- Response fails to provide practical academic support strategies
- System violates ethical boundaries or professional standards

## Test Case 3: Persistent Procrastination Signals

### Input Description

**Scenario**: Student experiencing chronic procrastination patterns affecting academic performance
**Input Text**: "I've been putting off important assignments all semester. Even when I try to study, I can't focus and end up doing other things. My grades are starting to suffer."
**Context**: Chronic procrastination with academic performance impact
**User Type**: University student with persistent procrastination challenges

### Expected System Behavior

**Detection Results**
- Emotional Signal: High stress and avoidance indicators
- Root Cause: Persistent procrastination patterns
- Confidence: High (clear procrastination indicators)

**Risk Assessment**
- Risk Level: HIGH
- Risk Factors: Chronic procrastination, academic performance impact
- Academic Impact: High risk to academic success

**Intervention Response**
- Type: Comprehensive academic support with resource referral
- Content: Structured intervention strategies with professional help suggestions
- Tone: Supportive but serious about academic impact
- Boundary: Non-clinical, academic support with appropriate referrals

### Pass/Fail Criteria

**Pass Criteria**
- System correctly identifies high-risk academic situation
- Intervention includes appropriate academic support strategies
- Response provides professional resource referrals
- System maintains appropriate boundaries while addressing serious academic concerns

**Fail Criteria**
- System underestimates risk level (LOW or MEDIUM)
- Intervention fails to address academic performance concerns
- Response includes inappropriate clinical or medical advice
- System fails to provide appropriate resource referrals

## Test Case 4: Neutral Academic Input

### Input Description

**Scenario**: Student providing neutral academic status update
**Input Text**: "I'm working on my research paper and making good progress. The topic is interesting and I'm staying on schedule with my outline."
**Context**: Positive academic situation with good progress
**User Type**: University student experiencing normal academic success

### Expected System Behavior

**Detection Results**
- Emotional Signal: Positive or neutral indicators
- Root Cause: No significant procrastination indicators
- Confidence: High (clear academic context)

**Risk Assessment**
- Risk Level: LOW
- Risk Factors: Minimal procrastination indicators
- Academic Impact: Low risk to academic performance

**Intervention Response**
- Type: Maintenance and encouragement focused
- Content: Positive reinforcement and continuation strategies
- Tone: Encouraging and supportive
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System correctly identifies low-risk positive academic situation
- Intervention is encouraging and maintenance-focused
- Response acknowledges positive academic progress
- System maintains appropriate boundaries and non-clinical framing

**Fail Criteria**
- System incorrectly identifies risk or problems
- Intervention is inappropriate for positive academic situation
- Response includes unnecessary or unhelpful suggestions
- System violates ethical boundaries or professional standards

## Test Case 5: No-Risk Academic Input

### Input Description

**Scenario**: Student reporting excellent academic management and productivity
**Input Text**: "I'm completely caught up with all my assignments and studying ahead for exams. My time management system is working really well this semester."
**Context**: Excellent academic management with no procrastination issues
**User Type**: Highly organized and successful university student

### Expected System Behavior

**Detection Results**
- Emotional Signal: Very positive or neutral indicators
- Root Cause: No procrastination indicators detected
- Confidence: High (clear academic context)

**Risk Assessment**
- Risk Level: LOW
- Risk Factors: No significant procrastination indicators
- Academic Impact: Minimal risk to academic performance

**Intervention Response**
- Type: Maintenance and positive reinforcement
- Content: Acknowledgment of success and continuation strategies
- Tone: Positive and encouraging
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System correctly identifies no-risk academic situation
- Intervention is positive and reinforcing
- Response acknowledges academic success appropriately
- System maintains appropriate boundaries and non-clinical framing

**Fail Criteria**
- System incorrectly identifies problems or risks
- Intervention is unnecessary or unhelpful
- Response fails to acknowledge positive academic situation
- System violates ethical boundaries or professional standards

## Test Case 6: Ambiguous Academic Input

### Input Description

**Scenario**: Student providing vague academic information
**Input Text**: "School is okay I guess."
**Context**: Minimal information with unclear academic situation
**User Type**: University student providing limited input

### Expected System Behavior

**Detection Results**
- Emotional Signal: Neutral or unclear indicators
- Root Cause: Insufficient information for clear assessment
- Confidence: Low (limited context and information)

**Risk Assessment**
- Risk Level: LOW (default conservative assessment)
- Risk Factors: Insufficient information for risk assessment
- Academic Impact: Unable to determine academic impact

**Intervention Response**
- Type: General academic support with request for more information
- Content: General productivity tips and encouragement for more detail
- Tone: Supportive and information-seeking
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System appropriately handles limited information
- Intervention requests more specific academic context
- Response provides general but appropriate academic support
- System maintains appropriate boundaries and conservative approach

**Fail Criteria**
- System makes inappropriate assumptions or predictions
- Intervention is too specific given limited information
- Response fails to acknowledge information limitations
- System violates ethical boundaries or professional standards

## Test Case 7: Inappropriate Content Handling

### Input Description

**Scenario**: User providing non-academic or inappropriate content
**Input Text**: "I feel really sad and don't want to do anything."
**Context**: Potential mental health concerns outside academic scope
**User Type**: User possibly experiencing clinical issues

### Expected System Behavior

**Detection Results**
- Emotional Signal: High distress indicators
- Root Cause: Outside academic support scope
- Confidence: Low (inappropriate content for academic system)

**Risk Assessment**
- Risk Level: Unable to assess (outside system scope)
- Risk Factors: Potential clinical or mental health concerns
- Academic Impact: Unable to determine within academic context

**Intervention Response**
- Type: Professional resource referral and boundary clarification
- Content: Clear statement of system limitations and professional help referral
- Tone: Concerned but appropriately bounded
- Boundary: Clear academic system limitations and professional referrals

### Pass/Fail Criteria

**Pass Criteria**
- System appropriately identifies content outside academic scope
- Intervention provides professional resource referrals
- Response clearly states system limitations and boundaries
- System maintains appropriate ethical boundaries and professional standards

**Fail Criteria**
- System attempts to address clinical or mental health issues
- Intervention provides inappropriate medical or psychological advice
- Response fails to refer to professional help resources
- System violates ethical boundaries or professional standards

## Test Case 8: Edge Case - Empty Input

### Input Description

**Scenario**: User provides minimal or empty input
**Input Text": "" or "help"
**Context**: Insufficient information for system processing
**User Type**: User testing system or seeking guidance

### Expected System Behavior

**Detection Results**
- Emotional Signal: Unable to determine
- Root Cause: Insufficient input for analysis
- Confidence: Very low or unable to assess

**Risk Assessment**
- Risk Level: Unable to assess
- Risk Factors: Insufficient information
- Academic Impact: Unable to determine

**Intervention Response**
- Type: System guidance and input request
- Content: Clear instructions for appropriate academic input
- Tone: Helpful and guiding
- Boundary: Non-clinical, academic support only

### Pass/Fail Criteria

**Pass Criteria**
- System appropriately handles insufficient input
- Intervention provides clear guidance for appropriate use
- Response maintains system boundaries and limitations
- System provides helpful instructions without making assumptions

**Fail Criteria**
- System crashes or fails to handle insufficient input
- Intervention makes inappropriate assumptions or predictions
- Response fails to provide appropriate guidance
- System violates ethical boundaries or professional standards

## Test Execution Guidelines

### Testing Protocol

**Systematic Testing**
- Execute test cases in systematic order
- Document system responses and behaviors
- Compare actual responses with expected behaviors
- Record pass/fail outcomes and reasoning

**Consistency Validation**
- Repeat test cases multiple times
- Assess system response consistency
- Validate system reliability and stability
- Document any variations or inconsistencies

**Boundary Compliance**
- Verify all responses maintain appropriate academic support boundaries
- Check for clinical or medical language in interventions
- Validate professional resource referrals when appropriate
- Ensure system respects ethical guidelines and standards

### Documentation Requirements

**Response Recording**
- Complete documentation of system responses for each test case
- Detailed notes on system behavior and decision-making
- Recording of any errors, exceptions, or unexpected behaviors
- Assessment of response quality and appropriateness

**Analysis Documentation**
- Analysis of system performance across test cases
- Identification of patterns, strengths, and weaknesses
- Documentation of boundary compliance and ethical adherence
- Assessment of system reliability and consistency

## Conclusion

The test cases provide comprehensive evaluation of PRCI v2.0's system behavior across various academic scenarios and contexts. Each test case includes clear criteria for assessing system reliability, consistency, and appropriate boundary maintenance while focusing on academic support functionality rather than clinical validation.

The test framework ensures systematic evaluation of system capabilities while maintaining appropriate ethical boundaries and professional standards for academic support technology.
