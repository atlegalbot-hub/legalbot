// Application constants

export const CLASSES = ['8th', '9th', '10th', '11th', '12th'];

export const CONSTITUTION_TOPICS = {
  HISTORY: 'history',
  FUNDAMENTAL_RIGHTS: 'fundamental_rights',
  DIRECTIVE_PRINCIPLES: 'directive_principles',
  FUNDAMENTAL_DUTIES: 'fundamental_duties',
  AMENDMENT_PROCESS: 'amendment_process',
  GOVERNMENT_STRUCTURE: 'government_structure',
  JUDICIARY: 'judiciary',
  FEDERALISM: 'federalism',
};

export const FEEDBACK_SCORES = {
  VERY_POOR: 1,
  POOR: 2,
  AVERAGE: 3,
  GOOD: 4,
  EXCELLENT: 5,
};

export const SAMPLE_QUESTIONS = [
  "Who is known as the Father of Indian Constitution?",
  "What are the Fundamental Rights?",
  "Explain the amendment process",
  "What is the Preamble of Indian Constitution?",
  "Difference between Fundamental Rights and Directive Principles",
  "What are Fundamental Duties?",
  "How was the Constituent Assembly formed?",
  "Explain the federal structure of India",
  "What is the role of Supreme Court?",
  "Constitutional remedies under Article 32"
];

export const CONSTITUTION_FACTS = [
  "The Indian Constitution is the longest written constitution in the world",
  "It took 2 years, 11 months, and 18 days to draft the Constitution",
  "Dr. B.R. Ambedkar is known as the Father of Indian Constitution",
  "The Constitution was adopted on November 26, 1949",
  "It came into effect on January 26, 1950 (Republic Day)",
  "The original Constitution was handwritten in Hindi and English",
  "It has 395 articles and 12 schedules currently",
  "The Preamble was amended only once by the 42nd Amendment in 1976"
];

export const LEARNING_LEVELS = {
  '8th': {
    title: 'Class 8th - Foundation',
    description: 'Basic concepts and introduction to Constitution',
    topics: ['History', 'Basic Rights', 'Key Personalities']
  },
  '9th': {
    title: 'Class 9th - Understanding',
    description: 'Fundamental principles and democratic values',
    topics: ['Fundamental Rights', 'Democracy', 'Citizenship']
  },
  '10th': {
    title: 'Class 10th - Application',
    description: 'Practical understanding and real-world connections',
    topics: ['Rights & Duties', 'Government Functions', 'Legal System']
  },
  '11th': {
    title: 'Class 11th - Analysis',
    description: 'Detailed study and critical thinking',
    topics: ['Political System', 'Federalism', 'Judiciary']
  },
  '12th': {
    title: 'Class 12th - Evaluation',
    description: 'Contemporary issues and advanced concepts',
    topics: ['Amendments', 'Challenges', 'Comparative Study']
  }
};

export const UI_CONSTANTS = {
  ANIMATION_DURATION: 300,
  TYPING_SPEED: 50,
  MAX_MESSAGE_LENGTH: 1000,
  PAGINATION_SIZE: 10,
  SEARCH_DEBOUNCE: 300,
};

export default {
  CLASSES,
  CONSTITUTION_TOPICS,
  FEEDBACK_SCORES,
  SAMPLE_QUESTIONS,
  CONSTITUTION_FACTS,
  LEARNING_LEVELS,
  UI_CONSTANTS,
};