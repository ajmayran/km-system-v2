from django.core.management.base import BaseCommand
from chatbot.spell_corrector import get_spell_corrector, get_spell_correction_stats

class Command(BaseCommand):
    help = 'Show spell checker statistics and manage learned patterns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-patterns',
            action='store_true',
            help='Save currently learned patterns to file'
        )
        parser.add_argument(
            '--test-correction',
            type=str,
            help='Test spell correction on a specific phrase'
        )

    def handle(self, *args, **options):
        corrector = get_spell_corrector()
        
        if options['save_patterns']:
            corrector.save_learned_patterns()
            self.stdout.write(
                self.style.SUCCESS('✅ Saved learned patterns to file')
            )
        
        if options['test_correction']:
            original = options['test_correction']
            corrected = corrector.correct_spelling(original)
            self.stdout.write(f"Original: {original}")
            self.stdout.write(f"Corrected: {corrected}")
            if original != corrected:
                self.stdout.write(self.style.SUCCESS("✅ Correction applied"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ No correction needed"))
        
        # Show statistics
        stats = get_spell_correction_stats()
        
        self.stdout.write("\n📊 Spell Correction Statistics:")
        self.stdout.write(f"Total corrections made: {stats['total_corrections']}")
        self.stdout.write(f"Pattern-based corrections: {stats['pattern_corrections']}")
        self.stdout.write(f"Algorithmic corrections: {stats['algorithmic_corrections']}")
        self.stdout.write(f"Cache hits: {stats['cache_hits']}")
        self.stdout.write(f"Learned patterns: {stats['learned_patterns_count']}")
        self.stdout.write(f"Knowledge vocabulary size: {stats['knowledge_vocabulary_size']}")
        self.stdout.write(f"Pattern efficiency: {stats['pattern_efficiency']:.1f}%")