import re
import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict

class ContentAnalyzer:
    def __init__(self):
        self.todo_patterns = [
            r'(?:TODO|To-?do|ACTION|Action|TASK|Task):\s*(.+)',
            r'[-*•]\s*\[?\s*\]?\s*(.+)',
            r'(?:\d+\.|\w\))\s*(.+)',
            r'→\s*(.+)',  # Arrow indicators
            r'⭐\s*(.+)',  # Star indicators
        ]
        
        self.priority_keywords = {
            'high': ['urgent', 'asap', 'critical', 'important', 'priority', 'deadline'],
            'medium': ['soon', 'next week', 'follow up', 'check', 'review'],
            'low': ['later', 'eventually', 'consider', 'maybe', 'optional']
        }
    
    def structure_content(self, raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure and enhance the raw analysis from Doubao
        """
        try:
            # Start with the raw analysis
            structured = raw_analysis.copy()
            
            # Enhance action items with priorities
            if 'action_items' in structured:
                structured['action_items'] = self._enhance_action_items(structured['action_items'])
            
            # Create hierarchical structure for mind mapping
            structured['hierarchy'] = self._create_hierarchy(structured)
            
            # Extract key concepts and relationships
            structured['concepts'] = self._extract_concepts(structured)
            
            # Generate meeting insights
            structured['insights'] = self._generate_insights(structured)
            
            # Add content statistics
            structured['statistics'] = self._calculate_statistics(structured)
            
            return structured
            
        except Exception as e:
            print(f"Content structuring failed: {e}")
            return raw_analysis
    
    def cluster_content(self, sections: List[Dict]) -> List[Dict]:
        """
        Group related content using keyword similarity
        """
        try:
            clusters = []
            used_sections = set()
            
            for i, section in enumerate(sections):
                if i in used_sections:
                    continue
                
                cluster = {
                    'title': section.get('heading', f'Topic {len(clusters) + 1}'),
                    'sections': [section],
                    'keywords': self._extract_keywords(section.get('content', ''))
                }
                
                # Find related sections
                for j, other_section in enumerate(sections):
                    if j <= i or j in used_sections:
                        continue
                    
                    if self._are_related(cluster['keywords'], 
                                       self._extract_keywords(other_section.get('content', ''))):
                        cluster['sections'].append(other_section)
                        used_sections.add(j)
                
                used_sections.add(i)
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            print(f"Content clustering failed: {e}")
            return sections
    
    def extract_todos(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract and categorize action items from text
        """
        todos = []
        
        for pattern in self.todo_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                task_text = match.group(1).strip()
                if len(task_text) > 5:  # Filter out very short matches
                    todo = {
                        'task': task_text,
                        'priority': self._determine_priority(task_text),
                        'assignee': self._extract_assignee(task_text),
                        'deadline': self._extract_deadline(task_text),
                        'category': self._categorize_task(task_text)
                    }
                    todos.append(todo)
        
        # Remove duplicates based on task similarity
        return self._deduplicate_todos(todos)
    
    def generate_hierarchy(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create hierarchical structure for mind maps
        """
        try:
            root = {
                'name': content.get('title', 'Meeting Notes'),
                'children': []
            }
            
            # Add main sections as top-level branches
            for section in content.get('sections', []):
                section_node = {
                    'name': section.get('heading', 'Section'),
                    'type': 'section',
                    'children': []
                }
                
                # Add subsections
                for subsection in section.get('subsections', []):
                    subsection_node = {
                        'name': subsection.get('heading', 'Subsection'),
                        'type': 'subsection',
                        'content': subsection.get('content', '')[:100] + '...' if len(subsection.get('content', '')) > 100 else subsection.get('content', '')
                    }
                    section_node['children'].append(subsection_node)
                
                root['children'].append(section_node)
            
            # Add action items as a separate branch
            if content.get('action_items'):
                action_branch = {
                    'name': 'Action Items',
                    'type': 'actions',
                    'children': []
                }
                
                for item in content['action_items']:
                    action_node = {
                        'name': item.get('task', 'Task')[:50] + '...' if len(item.get('task', '')) > 50 else item.get('task', ''),
                        'type': 'task',
                        'priority': item.get('priority', 'medium'),
                        'assignee': item.get('assignee')
                    }
                    action_branch['children'].append(action_node)
                
                root['children'].append(action_branch)
            
            # Add key points branch
            if content.get('key_points'):
                key_points_branch = {
                    'name': 'Key Points',
                    'type': 'keypoints',
                    'children': []
                }
                
                for point in content['key_points']:
                    point_node = {
                        'name': point[:60] + '...' if len(point) > 60 else point,
                        'type': 'point'
                    }
                    key_points_branch['children'].append(point_node)
                
                root['children'].append(key_points_branch)
            
            return root
            
        except Exception as e:
            print(f"Hierarchy generation failed: {e}")
            return {'name': 'Meeting Notes', 'children': []}
    
    def identify_key_concepts(self, text: str) -> List[str]:
        """
        Extract main topics and keywords from text
        """
        # Simple keyword extraction
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]+\b', text.lower())
        
        # Filter common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1
        
        # Return top concepts
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:20]
    
    def _enhance_action_items(self, action_items: List[Dict]) -> List[Dict]:
        """
        Enhance action items with better categorization and priorities
        """
        enhanced = []
        
        for item in action_items:
            enhanced_item = item.copy()
            
            task_text = item.get('task', '')
            
            # Improve priority detection
            if not enhanced_item.get('priority'):
                enhanced_item['priority'] = self._determine_priority(task_text)
            
            # Extract assignee if not present
            if not enhanced_item.get('assignee'):
                enhanced_item['assignee'] = self._extract_assignee(task_text)
            
            # Extract deadline
            enhanced_item['deadline'] = self._extract_deadline(task_text)
            
            # Categorize task
            enhanced_item['category'] = self._categorize_task(task_text)
            
            # Estimate effort
            enhanced_item['effort'] = self._estimate_effort(task_text)
            
            enhanced.append(enhanced_item)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        enhanced.sort(key=lambda x: priority_order.get(x.get('priority', 'medium'), 1))
        
        return enhanced
    
    def _determine_priority(self, task_text: str) -> str:
        """
        Determine task priority based on keywords
        """
        task_lower = task_text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                return priority
        
        # Default priority based on text characteristics
        if any(word in task_lower for word in ['must', 'need', 'required', 'asap']):
            return 'high'
        elif any(word in task_lower for word in ['should', 'want', 'prefer']):
            return 'medium'
        else:
            return 'low'
    
    def _extract_assignee(self, task_text: str) -> str:
        """
        Extract assignee from task text
        """
        # Look for patterns like "@John", "assigned to John", "John will"
        assignee_patterns = [
            r'@([A-Za-z]+)',
            r'assigned to ([A-Za-z]+)',
            r'([A-Za-z]+) will',
            r'([A-Za-z]+) should',
            r'([A-Za-z]+) needs to'
        ]
        
        for pattern in assignee_patterns:
            match = re.search(pattern, task_text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None
    
    def _extract_deadline(self, task_text: str) -> str:
        """
        Extract deadline information from task text
        """
        deadline_patterns = [
            r'by ([A-Za-z]+ \d+)',
            r'due ([A-Za-z]+ \d+)',
            r'deadline ([A-Za-z]+ \d+)',
            r'(next week|this week|tomorrow|today)',
            r'(\d+/\d+/\d+)',
            r'(\d+-\d+-\d+)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, task_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _categorize_task(self, task_text: str) -> str:
        """
        Categorize task based on content
        """
        categories = {
            'development': ['code', 'develop', 'build', 'implement', 'program', 'debug'],
            'research': ['research', 'investigate', 'study', 'analyze', 'explore'],
            'communication': ['email', 'call', 'meeting', 'discuss', 'contact', 'inform'],
            'documentation': ['document', 'write', 'update', 'record', 'note'],
            'testing': ['test', 'verify', 'validate', 'check', 'review'],
            'planning': ['plan', 'schedule', 'organize', 'prepare', 'setup']
        }
        
        task_lower = task_text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in task_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _estimate_effort(self, task_text: str) -> str:
        """
        Estimate effort required for task
        """
        task_lower = task_text.lower()
        
        high_effort_keywords = ['develop', 'build', 'create', 'design', 'implement', 'research']
        medium_effort_keywords = ['update', 'modify', 'review', 'analyze', 'test']
        low_effort_keywords = ['call', 'email', 'check', 'ask', 'inform']
        
        if any(keyword in task_lower for keyword in high_effort_keywords):
            return 'high'
        elif any(keyword in task_lower for keyword in medium_effort_keywords):
            return 'medium'
        elif any(keyword in task_lower for keyword in low_effort_keywords):
            return 'low'
        else:
            return 'medium'  # default
    
    def _create_hierarchy(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create hierarchical structure for content
        """
        return self.generate_hierarchy(content)
    
    def _extract_concepts(self, content: Dict[str, Any]) -> List[str]:
        """
        Extract key concepts from structured content
        """
        all_text = content.get('raw_text', '')
        
        # Add text from sections
        for section in content.get('sections', []):
            all_text += ' ' + section.get('content', '')
        
        return self.identify_key_concepts(all_text)
    
    def _generate_insights(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights from the content
        """
        insights = {
            'meeting_type': self._determine_meeting_type(content),
            'main_themes': self._extract_themes(content),
            'decision_points': self._extract_decisions(content),
            'open_questions': self._extract_questions(content),
            'next_steps': self._extract_next_steps(content)
        }
        
        return insights
    
    def _calculate_statistics(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate content statistics
        """
        stats = {
            'total_sections': len(content.get('sections', [])),
            'total_action_items': len(content.get('action_items', [])),
            'high_priority_items': len([item for item in content.get('action_items', []) if item.get('priority') == 'high']),
            'total_key_points': len(content.get('key_points', [])),
            'tables_count': len(content.get('tables', [])),
            'diagrams_count': len(content.get('diagrams', [])),
            'word_count': len(content.get('raw_text', '').split()) if content.get('raw_text') else 0,
            'estimated_reading_time': max(1, len(content.get('raw_text', '').split()) // 200) if content.get('raw_text') else 1
        }
        
        return stats
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for clustering
        """
        return self.identify_key_concepts(text)[:10]
    
    def _are_related(self, keywords1: List[str], keywords2: List[str]) -> bool:
        """
        Determine if two sets of keywords are related
        """
        if not keywords1 or not keywords2:
            return False
        
        common_keywords = set(keywords1) & set(keywords2)
        return len(common_keywords) >= max(1, min(len(keywords1), len(keywords2)) * 0.3)
    
    def _deduplicate_todos(self, todos: List[Dict]) -> List[Dict]:
        """
        Remove duplicate action items based on similarity
        """
        if not todos:
            return todos
        
        unique_todos = []
        
        for todo in todos:
            is_duplicate = False
            for unique_todo in unique_todos:
                if self._tasks_similar(todo['task'], unique_todo['task']):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_todos.append(todo)
        
        return unique_todos
    
    def _tasks_similar(self, task1: str, task2: str) -> bool:
        """
        Check if two tasks are similar
        """
        # Simple similarity check based on word overlap
        words1 = set(task1.lower().split())
        words2 = set(task2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        min_words = min(len(words1), len(words2))
        
        return overlap / min_words > 0.6
    
    def _determine_meeting_type(self, content: Dict) -> str:
        """
        Determine the type of meeting based on content
        """
        text = content.get('raw_text', '').lower()
        
        if any(word in text for word in ['standup', 'daily', 'scrum']):
            return 'standup'
        elif any(word in text for word in ['retrospective', 'retro', 'review']):
            return 'retrospective'
        elif any(word in text for word in ['planning', 'roadmap', 'strategy']):
            return 'planning'
        elif any(word in text for word in ['brainstorm', 'ideation', 'creative']):
            return 'brainstorming'
        elif any(word in text for word in ['decision', 'vote', 'choose']):
            return 'decision_making'
        else:
            return 'general'
    
    def _extract_themes(self, content: Dict) -> List[str]:
        """
        Extract main themes from content
        """
        concepts = content.get('concepts', [])
        return concepts[:5]  # Top 5 themes
    
    def _extract_decisions(self, content: Dict) -> List[str]:
        """
        Extract decision points from content
        """
        text = content.get('raw_text', '')
        decision_patterns = [
            r'decided to (.+)',
            r'decision: (.+)',
            r'we will (.+)',
            r'agreed to (.+)',
            r'conclusion: (.+)'
        ]
        
        decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decisions.extend(matches)
        
        return decisions[:5]  # Top 5 decisions
    
    def _extract_questions(self, content: Dict) -> List[str]:
        """
        Extract open questions from content
        """
        text = content.get('raw_text', '')
        questions = re.findall(r'([^.!?]*\?)', text)
        
        # Filter and clean questions
        cleaned_questions = []
        for question in questions:
            question = question.strip()
            if len(question) > 10 and len(question) < 200:
                cleaned_questions.append(question + '?')
        
        return cleaned_questions[:5]
    
    def _extract_next_steps(self, content: Dict) -> List[str]:
        """
        Extract next steps from content
        """
        action_items = content.get('action_items', [])
        high_priority_items = [item['task'] for item in action_items if item.get('priority') == 'high']
        
        return high_priority_items[:3]  # Top 3 next steps