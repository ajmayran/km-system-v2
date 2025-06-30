from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chatbot.models import ChatSession, ChatMessage
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up expired chat sessions and their associated messages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Delete sessions older than X days (default: 1 day)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_old = options['days']
        force = options['force']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(days=days_old)
        
        # Find expired sessions
        expired_sessions = ChatSession.objects.filter(expires_at__lt=timezone.now())
        old_sessions = ChatSession.objects.filter(created_at__lt=cutoff_time)
        
        # Get counts for reporting
        expired_count = expired_sessions.count()
        old_count = old_sessions.count()
        
        # Get message counts
        expired_messages = ChatMessage.objects.filter(session__in=expired_sessions)
        old_messages = ChatMessage.objects.filter(session__in=old_sessions)
        
        expired_msg_count = expired_messages.count()
        old_msg_count = old_messages.count()
        
        # Report what will be cleaned
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.WARNING("🧹 CHATBOT SESSION CLEANUP REPORT"))
        self.stdout.write("="*60)
        
        self.stdout.write(f"📅 Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"⏰ Current time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("")
        
        # Expired sessions (past expiry date)
        if expired_count > 0:
            self.stdout.write(self.style.ERROR(f"🕐 Expired sessions (past expiry): {expired_count}"))
            self.stdout.write(f"   📨 Associated messages: {expired_msg_count}")
            
            if not dry_run:
                self.stdout.write("   Sessions to delete:")
                for session in expired_sessions[:5]:  # Show first 5
                    self.stdout.write(f"     - {session.session_id} (expired: {session.expires_at})")
                if expired_count > 5:
                    self.stdout.write(f"     ... and {expired_count - 5} more")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No expired sessions found"))
        
        # Old sessions (older than specified days)
        if old_count > 0:
            self.stdout.write(self.style.WARNING(f"📅 Old sessions (>{days_old} days): {old_count}"))
            self.stdout.write(f"   📨 Associated messages: {old_msg_count}")
            
            if not dry_run:
                self.stdout.write("   Sessions to delete:")
                for session in old_sessions[:5]:  # Show first 5
                    self.stdout.write(f"     - {session.session_id} (created: {session.created_at})")
                if old_count > 5:
                    self.stdout.write(f"     ... and {old_count - 5} more")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ No sessions older than {days_old} days found"))
        
        # Total summary
        total_sessions = expired_count + old_count
        total_messages = expired_msg_count + old_msg_count
        
        if total_sessions == 0:
            self.stdout.write("\n" + self.style.SUCCESS("🎉 No cleanup needed! All sessions are current."))
            return
        
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"📊 TOTAL TO DELETE:"))
        self.stdout.write(f"   🗂️  Sessions: {total_sessions}")
        self.stdout.write(f"   📨 Messages: {total_messages}")
        
        # Show current database stats
        total_all_sessions = ChatSession.objects.count()
        total_all_messages = ChatMessage.objects.count()
        self.stdout.write("")
        self.stdout.write(f"📈 CURRENT DATABASE STATS:")
        self.stdout.write(f"   🗂️  Total sessions: {total_all_sessions}")
        self.stdout.write(f"   📨 Total messages: {total_all_messages}")
        
        if dry_run:
            self.stdout.write("\n" + self.style.WARNING("🔍 DRY RUN MODE - Nothing was deleted"))
            self.stdout.write("Run without --dry-run to perform actual cleanup")
            return
        
        # Confirmation prompt
        if not force:
            self.stdout.write("\n" + "="*60)
            confirm = input(self.style.ERROR("⚠️  Are you sure you want to delete these sessions? (y/N): "))
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.WARNING("❌ Cleanup cancelled"))
                return
        
        # Perform deletion
        self.stdout.write("\n" + self.style.WARNING("🗑️  Starting cleanup..."))
        
        deleted_counts = {'sessions': 0, 'messages': 0}
        
        try:
            # Delete expired sessions (this will cascade to messages)
            if expired_count > 0:
                self.stdout.write(f"Deleting {expired_count} expired sessions...")
                deleted_sessions, session_details = expired_sessions.delete()
                deleted_counts['sessions'] += expired_count
                deleted_counts['messages'] += session_details.get('chatbot.ChatMessage', 0)
                self.stdout.write(self.style.SUCCESS(f"✅ Deleted {expired_count} expired sessions"))
            
            # Delete old sessions (this will cascade to messages)
            if old_count > 0:
                self.stdout.write(f"Deleting {old_count} old sessions...")
                deleted_sessions, session_details = old_sessions.delete()
                deleted_counts['sessions'] += old_count
                deleted_counts['messages'] += session_details.get('chatbot.ChatMessage', 0)
                self.stdout.write(self.style.SUCCESS(f"✅ Deleted {old_count} old sessions"))
            
            # Final report
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS("🎉 CLEANUP COMPLETED SUCCESSFULLY!"))
            self.stdout.write("="*60)
            self.stdout.write(f"🗑️  Sessions deleted: {deleted_counts['sessions']}")
            self.stdout.write(f"📨 Messages deleted: {deleted_counts['messages']}")
            
            # Show updated database stats
            remaining_sessions = ChatSession.objects.count()
            remaining_messages = ChatMessage.objects.count()
            self.stdout.write("")
            self.stdout.write(f"📊 UPDATED DATABASE STATS:")
            self.stdout.write(f"   🗂️  Remaining sessions: {remaining_sessions}")
            self.stdout.write(f"   📨 Remaining messages: {remaining_messages}")
            
            # Log the cleanup
            logger.info(f"Chatbot session cleanup: {deleted_counts['sessions']} sessions, {deleted_counts['messages']} messages deleted")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during cleanup: {str(e)}"))
            logger.error(f"Chatbot session cleanup error: {str(e)}")
            
        self.stdout.write("="*60)