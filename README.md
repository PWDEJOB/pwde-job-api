# PWDE-JOB MAIN API
A job board platform specifically designed for People with Disabilities (PWD)

## Overview
PWDE-JOB is a specialized job board platform that connects employers with qualified PWD candidates. The platform provides a comprehensive suite of features for both job seekers and employers, with a focus on accessibility and inclusivity.

**Click the badge to see api docuemantion**
(or check it yourself its in the docs folder)

[![Docs](https://img.shields.io/badge/docs-GitBook-brightgreen)](https://my-docuemnations.gitbook.io/pwde-job-api-documentation#authentication-endpoints)

## Features

### Job Seeker Features
- **Authentication**
  - Secure login and registration system
  - Profile management
  - Password recovery

- **Job Recommendations**
  - Personalized job matching
  - Skill-based recommendations
  - Location-based filtering

- **Profile Management**
  - Professional profile creation
  - Resume upload and management
  - Skills and experience tracking

- **Notifications**
  - Job application updates
  - New job matches
  - Interview invitations
  - System notifications

- **Application History**
  - Track job applications
  - View application status
  - Save favorite jobs

- **Settings**
  - Account preferences
  - Notification settings
  - Privacy controls

- **Messaging System**
  - Direct communication with employers
  - Interview scheduling
  - Application follow-ups

### Employer Features
- **Authentication**
  - Company account management
  - Admin access control

- **Job Listing Statistics**
  - Application analytics
  - Candidate insights
  - Performance metrics

- **Job Listings Management**
  - Create new job postings
  - Update existing listings
  - Delete expired positions
  - Draft management

- **Initial Test Management**
  - Create assessment tests
  - Review test results
  - Candidate evaluation

- **Messaging System**
  - Candidate communication
  - Interview coordination
  - Application feedback

### Integrations
- **Zoom Integration**
  - Video interview scheduling
  - Meeting management
  - Recording capabilities

- **Resume Screening**
  - Automated resume parsing
  - Skill matching
  - Candidate ranking

## Progress Tracking

### Overall Progress: 85% Complete

### Completed ✅
- [x] **Project initialization**
- [x] **Basic project structure**
- [x] **Authentication system** - FULLY IMPLEMENTED
  - [x] Employee signup (with file uploads)
  - [x] Employer signup (with company logo upload)
  - [x] Employee login
  - [x] Employer login
  - [x] Logout functionality
  - [x] Session management with Redis
- [x] **Database schema design**
- [x] **API endpoints planning and documentation**
- [x] **Profile management** - FULLY IMPLEMENTED
  - [x] Profile viewing (employee & employer)
  - [x] Profile updating (employee & employer)
  - [x] File upload support (profile pics, PWD IDs, company logos)
  - [x] Form validation and error handling
- [x] **Job Management System** - FULLY IMPLEMENTED
  - [x] Create jobs (with full job details)
  - [x] View all jobs
  - [x] View specific job details
  - [x] Delete jobs
  - [x] Update jobs
  - [x] PWD-friendly job marking
- [x] **Job Application System** - FULLY IMPLEMENTED
  - [x] Apply for jobs
  - [x] View job applicants
  - [x] Application history for employees
  - [x] Application status tracking
- [x] **Job Recommendation System** - FULLY IMPLEMENTED
  - [x] Skill-based matching algorithm
  - [x] PWD-friendly filtering
  - [x] Content-based and collaborative filtering
  - [x] Match scoring system
- [x] **Resume Management System** - FULLY IMPLEMENTED
  - [x] Resume upload (PDF only)
  - [x] File validation (type and size)
  - [x] Resume storage in Supabase
  - [x] Resume URL generation
- [x] **Application Status Management** - FULLY IMPLEMENTED
  - [x] Status tracking (under_review, accepted, rejected)
  - [x] Status updates by employers
  - [x] Application history viewing

### In Progress 🔄
- [ ] **Resume Screening System** - PARTIALLY IMPLEMENTED
  - [x] Basic resume upload and storage
  - [ ] Advanced text analysis
  - [ ] Automated skill extraction
  - [ ] Experience level detection
  - [ ] Education level detection
  - [ ] Advanced match scoring algorithms
- [ ] **Notification system** (Using Supabase Realtime)
- [ ] **Messaging system** (Using Supabase Realtime)
- [ ] **Employer dashboard analytics**
  - [ ] Application analytics
  - [ ] Candidate insights
  - [ ] Performance metrics
- [ ] **Advanced job search and filtering**
- [ ] **Email notifications**

### Upcoming Features 📋
- [ ] **Password reset system**
- [ ] **Email verification and confirmation**
- [ ] **Advanced job search and filters**
  - [ ] Location-based filtering
  - [ ] Salary range filtering
  - [ ] Industry filtering
  - [ ] Experience level filtering
- [ ] **Interview scheduling** (Using Zoom API integration)
- [ ] **Assessment/Test system** (Using Google Forms integration)
- [ ] **Email notification system**
- [ ] **Real-time messaging** (Using Supabase Realtime)
- [ ] **Push notifications** (Using Supabase Realtime)
- [ ] **Employer analytics dashboard**
- [ ] **Mobile app optimization**
- [ ] **API rate limiting and security enhancements**

## API Endpoints Summary

### 🔐 Authentication Endpoints (4/4 Complete)
- `POST /signupEmployee` - Employee registration with file uploads
- `POST /signupEmployer` - Employer registration with company logo
- `POST /login-employee` - Employee authentication
- `POST /login-employer` - Employer authentication
- `POST /logout` - Session termination

### 👤 Profile Management (3/3 Complete)
- `GET /view-profile` - View user profile (employee or employer)
- `POST /update-profile/employee` - Update employee profile
- `POST /update-profile/employer` - Update employer profile

### 👷 Employee Endpoints (4/4 Complete)
- `GET /reco-jobs` - Get personalized job recommendations
- `POST /upload-resume` - Upload/update resume (PDF only)
- `POST /apply-job/{job_id}` - Apply for specific job
- `GET /my-applications` - View application history

### 🏢 Employer Endpoints (7/7 Complete)
- `POST /create-jobs` - Create new job listing
- `GET /view-all-jobs` - View all employer's jobs
- `GET /view-job/{id}` - View specific job details
- `POST /update-job/{id}` - Update job listing
- `POST /delete-job/{id}` - Delete job listing
- `GET /job/{job_id}/applicants` - View job applicants
- `PATCH /application/{id}/status` - Update application status

### 📊 Total: 18 Endpoints Implemented

## Technical Stack
- **Backend**: Python (FastAPI)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth + Redis Sessions
- **File Storage**: Supabase Storage
- **API Framework**: FastAPI
- **Session Management**: Redis

## Getting Started
(To be added)

## Contributing
(To be added)

## License
(To be added)

## Contact
(To be added)

## Areas for Improvement

### Authentication System
1. Add password requirements (minimum length, special characters, etc.)
2. Add email verification system
3. Add "Forgot Password" feature
4. Add session timeout and auto-logout
5. Implement rate limiting for login attempts

### Job Management
1. Add pagination for job listings (show 10 jobs per page)
2. Add advanced search and filter options for jobs
3. Add job status (open/closed/filled)
4. Add job categories and tags
5. Add job location-based filtering

### Profile Management
1. Add profile picture upload
2. Add resume upload system with PDF processing
3. Implement proper skills storage as array
4. Add experience and education sections
5. Add profile completion percentage

### Resume Screening
1. Implement advanced text analysis
2. Add keyword extraction
3. Add experience level detection
4. Add education level detection
5. Implement more sophisticated matching algorithms

### Security
1. Add rate limiting to prevent spam
2. Add input validation to prevent bad data
3. Improve error messages
4. Add proper session management
5. Add API key validation

### API Structure
1. Make response formats consistent
2. Add API versioning (v1, v2, etc.)
3. Add proper error codes
4. Add request validation
5. Add API documentation

### Performance
1. Add caching for frequently accessed data
2. Optimize database queries
3. Add database indexes
4. Add request timeout handling
5. Add connection pooling

### User Experience
1. Add better error messages
2. Add loading states
3. Add success notifications
4. Add form validation
5. Add auto-save for forms

### Testing
1. Add unit tests
2. Add integration tests
3. Add API tests
4. Add security tests
5. Add performance tests

### Documentation
1. Add API usage examples
2. Add setup instructions
3. Add deployment guide
4. Add troubleshooting guide
5. Add contribution guidelines

veiw

