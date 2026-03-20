# Meeting Log

**Project:** Major Map
**Team:** SPG
**Semester:** Spring 2026

> **Time Commitment:** This is a 3-unit course. You should be working on this project **at least 6 hours per week** outside of meetings.

---

## Advisor Meetings

| Date | Duration | Format | Attendees | Summary | Action Items |
|------|----------|--------|-----------|---------|--------------|
| 1/28 | 30 min |  Remote | All | We had a recap on our project idea and updated the profesor on our progress. At this point we had created a front end prototype, done model testing, and built an API | Continue testing models, research deployments, continue working on frontend. |
| 2/11 | 30 min | Remote | All | We showed the professor the newer version of frontend, how to navigate through the pages. Explained the performance of our tree-based models versus neural network models. Showing professor that our backend is setted up through Swagger UI | Connecting backend and frontend. Clean up prediction models code. Fixing database.|
| 2/25 | 30 min | Remote | All | We asked for clarification on the project checkpoint assignment. We also briefly explained that we currently troubleshooting some of the issue that arose after connecting the backend and the frontend | Troubleshoot and fix bugs and errors related to the API and frontend/backend integration|
| 3/11 | 30 min | Remote | All | Full demo of our project. Professor approved our progress and work so far.| (Optional improvements by prof) Add some improvements like units for each course and semester, link courses to SJSU pages, generate schedules based on unit preference, link to electives page |
---

## Team Meetings

| Date | Duration | Format | Attendees | Summary | Action Items |
|------|----------|--------|-----------|---------|--------------|
| 2/6 | 1 hour  | Remote | All | Bryan setup the repository for GitHub classroom. We went over how to commit and push to GitHub classroom repository. We went over features we need to work on for next 2 weeks. | JSON Web tokens, frontend version 0, baseline neural network models.
| 2/13 | 1 hour  | Remote | All | Everyone updating on their progress. Bryan is still working on the JSON Web token and authentication page, Hoang and Anthony is still working on the neural network models, Pawandeep still working on the frontend | JSON Web tokens, frontend version 0, neural network models.
| 2/20 | 2 hours  | Remote | All | Bryan got the cookies system to work. Pawandeep is done with frontend verison 0. Hoang and Anthony finished the neural network models and compared them with the tree-based models. We found that the tree-based model performance is better and it doesn't wortht he compleixty to use neural network | Fix scheudle generation, tests for backend API
| 2/27 | 30 mins  | Remote | All | Short meeting, just updating our progress. | Demoable frontend version, more backend stuff, everyone goes over frontend and backend pipelines.|
| 3/2 | 1 hour  | Remote | All | Pawandeep demonstrated how to run the new frontend. Went over frontend folder and files. How to navigate and use each pages. Bryan went over the backend files and what need to be fix for the backend. Hoang and Anthony discussed on how to improve and approach the roadmap and schedule generation features | Demoable frontend version, more backend stuff, roadmap and schedules generations using ML models
| 3/6 | 30 min  | Remote | All | Just updating our progress with each other. Everyone will be busy for midterm next week | Demoable frontend version, more backend stuff, roadmap and schedules generations using ML models
| 3/7 | 4 hours  | Remote | All | We went over the new approach and the pipeline of get inputs, passed inputs into ML model, and generated the best slots | Program to candidate section, Update the ML model using Anthony's SVM model, Create an endpoint to test to prediction
| 3/8 | 8 hours | Remote | All | Worked on making ddl to import CSV data into MySQL. Added candidate section generation and integrated that with the ML Model for schedule generation. | Integrate schedule generation API endpoint with frontend. |
| 3/19 | 45 mins| Remote | All | Discussed the prototype video assignment and recorded it. Discussed future assignments, improvements, and plans for Implementation 3. | Work on roadmap features, search implmentation into DB, API, front loading, frontend |
---

## Meeting Notes (Only featuring meetings where significant discussion occured)

### 2/13 - Team Meeting

**Attendees:** All

**Discussion:** Every team member briefly talked about their current progress. Bryan talked about his progress so far on implementing the authentication page and JSON web token. Hoang and Anthony discussed their individual neural network models. Pawandeep said that he began working on the frontend.
-

**Decisions:** Since we weren't fully done with our assigned tasks, we decided to continue working on them and finish by the next time we meet up.
-

**Action Items:**
- [ ] Continue working on neural network model - Anthony - 2/20
- [ ] Implement JSON web token and authentication page - Bryan - 2/20
- [ ] Continue working on neural network model - Hoang - 2/20
- [ ] Implement the frontend - Pawandeep - 2/20

---

### 2/20 - Team Meeting

**Attendees:** All

**Discussion:** Each member showed their progression since the last meeting. Bryan showed how the cookies system worked. Pawandeep demoed the frontend version 0. Hoang and Anthony showed the neural network models and the results they found when compared to the tree-based models. 
-

**Decisions:** We decided that that we will use tree-based models as they performed better than neural network models. We also discussed what each member should be working on next.
-

**Action Items:**
- [ ] Fix ML predictive schedule generation and go over project pipline  - 2/28
- [ ] Create tests for backend API and go over project pipline  - Bryan - 2/28
- [ ] Fix ML predictive schedule generation and go over project pipline  - Hoang - 2/28
- [ ] Continue working on the frontend and go over project pipline - Pawandeep - 2/28

---

### 3/2 - Team Meeting

**Attendees:** All

**Discussion:** This was another meeting where each member showed their progress. Pawandeep demoed the full frontend UI implementation. Bryan discussed what needs to be fixed for the backend. Hoang and Anthony went over ways to improve the roadmap and schedule generation features.
-

**Decisions:** Our next goal was to integrate the frontend and backend and have a demoable prototype ready by the assigned date. 
-

**Action Items:**
- [ ] Integrate the frontend/backend and improve the roadmap and schedules page - Anthony - 3/6
- [ ] Integrate the frontend/backend and work on backend fixes - Bryan - 3/6
- [ ] Integrate the frontend/backend and improve the roadmap and schedules page - Hoang - 3/6
- [ ] Integrate the frontend/backend and work on frontend fixes - Pawandeep - 3/6

---

### 3/7 - Team Meeting

**Attendees:** All

**Discussion:** We discussed the new approach of getting course input for the upcoming semester, passing it into the ML model, and generating the best slots (more schedule options). 
-

**Decisions:** We decided that Hoang and Anthony will further work on improving the ML model. Bryan and Pawandeep will work on creating the schedule generation API endpoint for testing the ML model. 
-

**Action Items:**
- [ ] Program candidate section generation and update the ML model to SVM - Anthony - 3/9
- [ ] Create endpoint for testing the schedule generation  - Bryan - 3/9
- [ ] Program candidate section generation and update the ML model to SVM - Hoang - 3/9
- [ ] Create endpoint for testing the schedule generation - Pawandeep - 3/9

---

### 3/8 - Team Meeting

**Attendees:** All

**Discussion:** We worked on creating data definition language statements that import data from CSV format into our database. We also integrated candidate section generation with the ML model for predictive schedule generation.
-

**Decisions:** After improving the ML model, our next step is to integrate the API endpoint with the frontend schedule page and prepare our prototype demo that we will be showcasing to our advisor during the next meeting.
-

**Action Items:**
- [ ] Integrate schedule generation API endpoint with the frontend (for schedules page) and test the full prototype - Anthony - 3/11
- [ ] Prepare the prototype demo - Bryan - 3/11
- [ ] Integrate schedule generation API endpoint with the frontend (for schedules page) and test the full prototype - Hoang - 3/11
- [ ] Prepare the prototype demo - Pawandeep - 3/11

---

### 3/11 - Advisor Meeting

**Attendees:** All

**Discussion:** We demoed our project prototype to the advisor. He approved our project implementation so far and gave us feedback on some of the things he would like for us to implement. Those points of improvement include implementing a course unit system for each semester that would let users choose the amount of courses they would like to take, adding external links to SJSU's course information page for each course, and making some minor tweaks to the UI. 
-

**Decisions:** After the meeting, we decided that we would like to implement the unit system and external links. In addition to those changes, we also decided that we will look into adding external links to the Rate My Professor website for professor search and allow users to modify their generated roadmap to their liking.
-

**Action Items:**
- [ ] Work on allowing users to modify the roadmap - Anthony - 4/5
- [ ] Implement the external link feature for courses - Bryan - 4/5
- [ ] Work on the unit system - Hoang - 4/5
- [ ] Implement the external link feature for professor search - Pawandeep - 4/5

---
