import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

from chatbot.management.modules.database_loader import (
    load_knowledge_base_from_db,
    get_database_statistics,
    validate_database_connection
)

class Command(BaseCommand):
    help = 'Convert database knowledge base to JSON file for faster chatbot access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rebuild even if file exists',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Custom output path for JSON file',
            default=None
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate database connection before building',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show database statistics only',
        )

    def handle(self, *args, **options):
        # Show statistics if requested
        if options['stats']:
            self.show_database_stats()
            return
        
        # Validate database connection if requested
        if options['validate']:
            self.validate_database()
            return
        
        self.stdout.write(self.style.SUCCESS("🚀 Building JSON knowledge base from database..."))
        
        # Validate database connection first
        is_valid, message = validate_database_connection()
        if not is_valid:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))
            return
        
        # Define output path
        if options['output']:
            json_file_path = options['output']
        else:
            json_file_path = os.path.join(
                settings.BASE_DIR, 'chatbot', 'data', 'knowledge_base.json'
            )
        
        # Create directory if needed
        os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
        
        # Check if file exists
        if os.path.exists(json_file_path) and not options['force']:
            file_size = round(os.path.getsize(json_file_path) / (1024 * 1024), 2)
            modified_time = datetime.fromtimestamp(os.path.getmtime(json_file_path))
            
            self.stdout.write(
                self.style.WARNING(
                    f"❗ JSON file already exists:\n"
                    f"📁 Path: {json_file_path}\n"
                    f"💾 Size: {file_size} MB\n"
                    f"🕒 Modified: {modified_time}\n"
                    f"\nUse --force to overwrite or --output for different location"
                )
            )
            return
        
        try:
            # Load data using our separated database loader
            self.stdout.write("📊 Loading data from database...")
            knowledge_data, document_texts = load_knowledge_base_from_db()
            
            if not knowledge_data:
                self.stdout.write(self.style.ERROR("❌ No data found in database!"))
                return
            
            # Get database statistics
            db_stats = get_database_statistics()
            
            # Create comprehensive JSON structure
            json_data = {
                'metadata': {
                    'version': '1.0',
                    'generated_at': datetime.now().isoformat(),
                    'total_items': len(knowledge_data),
                    'document_count': len(document_texts),
                    'source': 'database_export',
                    'generator': 'build_knowledge_base_command',
                    'database_stats': db_stats
                },
                'knowledge_data': knowledge_data,
                'document_texts': document_texts,
                'statistics': self.calculate_content_statistics(knowledge_data)
            }
            
            # Write JSON file
            self.stdout.write(f"💾 Writing JSON to {json_file_path}...")
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            # Show success summary
            self.show_build_summary(json_file_path, json_data)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error building JSON: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def calculate_content_statistics(self, knowledge_data):
        """Calculate statistics about the content"""
        stats = {
            'content_types': {},
            'total_text_size': 0,
            'categories': {}
        }
        
        for item in knowledge_data:
            # Count by type
            content_type = item.get('type', 'unknown')
            stats['content_types'][content_type] = \
                stats['content_types'].get(content_type, 0) + 1
            
            # Count by category
            category = item.get('category', 'uncategorized')
            stats['categories'][category] = \
                stats['categories'].get(category, 0) + 1
            
            # Calculate text size
            text_size = len(item.get('title', '') + item.get('description', ''))
            stats['total_text_size'] += text_size
        
        return stats

    def show_database_stats(self):
        """Show database statistics"""
        self.stdout.write(self.style.SUCCESS("📊 Database Statistics:"))
        stats = get_database_statistics()
        
        for key, value in stats.items():
            self.stdout.write(f"  {key}: {value}")

    def validate_database(self):
        """Validate database connection"""
        is_valid, message = validate_database_connection()
        
        if is_valid:
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))

    def show_build_summary(self, file_path, json_data):
        """Show build completion summary"""
        file_size = os.path.getsize(file_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        metadata = json_data['metadata']
        stats = json_data['statistics']
        
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Knowledge Base JSON Built Successfully!\n"
            f"{'='*50}\n"
            f"📁 File: {file_path}\n"
            f"💾 Size: {file_size_mb} MB\n"
            f"📊 Total Items: {metadata['total_items']}\n"
            f"📄 Documents: {metadata['document_count']}\n"
            f"🕒 Generated: {metadata['generated_at']}\n"
            f"\n📋 Content Types:\n"
        ))
        
        for content_type, count in stats['content_types'].items():
            self.stdout.write(f"  • {content_type}: {count}")
        
        self.stdout.write(f"\n🚀 Your chatbot will now load {metadata['total_items']} items from JSON instead of database!")