"""
Database loader module for exporting knowledge base to JSON.
This module handles all database queries for building the knowledge base.
Used only during build-time, not runtime.
"""

from django.db import models
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

def load_knowledge_base_from_db():
    """
    Load all knowledge base data from database models.
    This is used ONLY for building JSON files, not for runtime queries.
    
    Returns:
        tuple: (knowledge_data, document_texts)
    """
    print("🔄 Loading knowledge base from database...")
    
    knowledge_data = []
    document_texts = []
    
    try:
        print("Loading knowledge base from database...")
        
        from appAdmin.models import (
            ResourceMetadata, KnowledgeResources, Commodity, Event,
            InformationSystem, Map, Media, News, Policy, Project,
            Publication, Technology, TrainingSeminar, Webinar, Product,
            CMI, AboutRationale, AboutObjective, AboutActivity, AboutTimeline, AboutTeamMember
        )
        from appCmi.models import Forum, FAQ
        
        # 1. Load Resource Metadata
        print("📊 Loading ResourceMetadata...")
        resources = ResourceMetadata.objects.filter(is_approved=True)
        print(f"Found {resources.count()} approved resources")
        
        for resource in resources:
            try:
                tags = [tag.name for tag in resource.tags.all()]
                commodities = [commodity.commodity_name for commodity in resource.commodities.all()]
                
                combined_text = f"{resource.title} {resource.description} {' '.join(tags)} {' '.join(commodities)}"
                
                knowledge_item = {
                    'id': f"resource_{resource.id}",
                    'actual_id': resource.id,
                    'title': resource.title,
                    'description': resource.description,
                    'type': 'resource',
                    'resource_type': resource.resource_type,
                    'slug': resource.slug,
                    'url': f'/cmis/knowledge-resources/post/{resource.slug}/',
                    'tags': tags,
                    'commodities': commodities,
                    'created_at': resource.created_at.isoformat() if resource.created_at else None,
                    'is_featured': resource.is_featured,
                    'raw_text': combined_text
                }
                
                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)
                
            except Exception as e:
                print(f"⚠️ Error processing resource {resource.id}: {e}")
                continue

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'resource'])} resources")

        # 2. Load Knowledge Categories
        print("📚 Loading KnowledgeResources...")
        knowledge_categories = KnowledgeResources.objects.filter(status='active')
        print(f"Found {knowledge_categories.count()} knowledge categories")
        
        for category in knowledge_categories:
            combined_text = f"{category.knowledge_title} {category.knowledge_description}"
            
            knowledge_item = {
                'id': f"category_{category.knowledge_id}",
                'actual_id': category.knowledge_id,
                'title': category.knowledge_title,
                'description': category.knowledge_description,
                'type': 'category',
                'slug': category.slug,
                'machine_name': category.machine_name,
                'url': f'/cmis/knowledge-resources/?type={category.machine_name}',
                'created_at': category.date_created.isoformat() if category.date_created else None,
                'raw_text': combined_text
            }
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'category'])} knowledge categories")

        # 3. Load Commodities
        print("🌾 Loading Commodities...")
        commodities = Commodity.objects.filter(status='active')
        print(f"Found {commodities.count()} commodities")
        
        for commodity in commodities:
            combined_text = f"{commodity.commodity_name} {commodity.description} {commodity.resources_type}"
            
            knowledge_item = {
                'id': f"commodity_{commodity.commodity_id}",
                'actual_id': commodity.commodity_id,
                'title': commodity.commodity_name,
                'description': commodity.description,
                'type': 'commodity',
                'slug': commodity.slug,
                'resources_type': commodity.resources_type,
                'url': f'/cmis/commodities/{commodity.slug}',
                'created_at': commodity.date_created.isoformat() if commodity.date_created else None,
                'latitude': float(commodity.latitude) if commodity.latitude else None,
                'longitude': float(commodity.longitude) if commodity.longitude else None,
                'raw_text': combined_text
            }
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'commodity'])} commodities")

        # 4. Load Events
        print("📅 Loading Events...")
        events = Event.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {events.count()} events")

        for event in events:
            combined_text = f"{event.metadata.title} {event.metadata.description} {event.location} {event.organizer}"

            knowledge_item = {
                'id': f"event_{event.id}",
                'actual_id': event.id,
                'title': event.metadata.title,
                'description': f"{event.metadata.description} Location: {event.location}, Organizer: {event.organizer}",
                'type': 'event',
                'slug': event.slug,
                'url': f'/cmis/knowledge-resources/events/{event.slug}/',
                'location': event.location,
                'organizer': event.organizer,
                'start_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                'end_date': event.end_date.strftime('%Y-%m-%d %H:%M'),
                'is_virtual': event.is_virtual,
                'created_at': event.metadata.created_at.isoformat() if event.metadata.created_at else None,
                'raw_text': combined_text
            }           

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'event'])} events")

        # 5. Load Information Systems
        print("💻 Loading Information Systems...")
        info_systems = InformationSystem.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {info_systems.count()} information systems")

        for info_system in info_systems:
            combined_text = f"{info_system.metadata.title} {info_system.metadata.description} {info_system.system_owner}"

            knowledge_item = {
                'id': f"info_system_{info_system.id}",
                'actual_id': info_system.id,
                'title': info_system.metadata.title,
                'description': f"{info_system.metadata.description} Owner: {info_system.system_owner}",
                'type': 'info_system',
                'slug': info_system.slug,
                'url': info_system.website_url,
                'system_owner': info_system.system_owner,
                'website_url': info_system.website_url,
                'last_updated': info_system.last_updated.strftime('%Y-%m-%d') if info_system.last_updated else None,
                'created_at': info_system.metadata.created_at.isoformat() if info_system.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'info_system'])} information systems")

        # 6. Load Maps
        print("🗺️ Loading Maps...")
        maps = Map.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {maps.count()} maps")

        for map_item in maps:
            combined_text = f"{map_item.metadata.title} {map_item.metadata.description}"

            knowledge_item = {
                'id': f"map_{map_item.id}",
                'actual_id': map_item.id,
                'title': map_item.metadata.title,
                'description': map_item.metadata.description,
                'type': 'map',
                'slug': map_item.slug,
                'url': f'/cmis/knowledge-resources/maps/{map_item.slug}/',
                'map_url': map_item.map_url,
                'latitude': float(map_item.latitude) if map_item.latitude else None,
                'longitude': float(map_item.longitude) if map_item.longitude else None,
                'created_at': map_item.metadata.created_at.isoformat() if map_item.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'map'])} maps")

        # 7. Load Media
        print("🎬 Loading Media...")
        media_items = Media.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {media_items.count()} media items")

        for media in media_items:
            combined_text = f"{media.metadata.title} {media.metadata.description} {media.author} {media.media_type}"

            knowledge_item = {
                'id': f"media_{media.id}",
                'actual_id': media.id,
                'title': media.metadata.title,
                'description': f"{media.metadata.description} Type: {media.media_type}, Author: {media.author}",
                'type': 'media',
                'slug': media.slug,
                'url': f'/cmis/knowledge-resources/media/{media.slug}/',
                'media_type': media.media_type,
                'author': media.author,
                'media_url': media.media_url,
                'created_at': media.metadata.created_at.isoformat() if media.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'media'])} media items")

        # 8. Load News
        print("📰 Loading News...")
        news_items = News.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {news_items.count()} news items")

        for news in news_items:
            combined_text = f"{news.metadata.title} {news.metadata.description} {news.content} {news.source}"

            knowledge_item = {
                'id': f"news_{news.id}",
                'actual_id': news.id,
                'title': news.metadata.title,
                'description': f"{news.content[:200]}... Source: {news.source}",
                'type': 'news',
                'slug': news.slug,
                'url': f'/cmis/knowledge-resources/news/{news.slug}/',
                'publication_date': news.publication_date.strftime('%Y-%m-%d'),
                'source': news.source,
                'external_url': news.external_url,
                'content': news.content,
                'created_at': news.metadata.created_at.isoformat() if news.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'news'])} news items")

        # 9. Load Policies
        print("📋 Loading Policies...")
        policies = Policy.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {policies.count()} policies")

        for policy in policies:
            combined_text = f"{policy.metadata.title} {policy.metadata.description} {policy.issuing_body} {policy.policy_number}"

            knowledge_item = {
                'id': f"policy_{policy.id}",
                'actual_id': policy.id,
                'title': policy.metadata.title,
                'description': f"{policy.metadata.description} Issued by: {policy.issuing_body}",
                'type': 'policy',
                'slug': policy.slug,
                'url': f'/cmis/knowledge-resources/policies/{policy.slug}/',
                'issuing_body': policy.issuing_body,
                'policy_number': policy.policy_number,
                'effective_date': policy.effective_date.strftime('%Y-%m-%d') if policy.effective_date else None,
                'status': policy.status,
                'policy_url': policy.policy_url,
                'created_at': policy.metadata.created_at.isoformat() if policy.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'policy'])} policies")

        # 10. Load Projects
        print("🌍 Loading Projects...")
        projects = Project.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {projects.count()} projects")

        for project in projects:
            combined_text = f"{project.metadata.title} {project.metadata.description} {project.project_lead} {project.funding_source}"

            knowledge_item = {
                'id': f"project_{project.id}",
                'actual_id': project.id,
                'title': project.metadata.title,
                'description': f"{project.metadata.description} Lead: {project.project_lead}",
                'type': 'project',
                'slug': project.slug,
                'url': f'/cmis/knowledge-resources/projects/{project.slug}/',
                'project_lead': project.project_lead,
                'start_date': project.start_date.strftime('%Y-%m-%d'),
                'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                'funding_source': project.funding_source,
                'status': project.status,
                'budget': float(project.budget) if project.budget else None,
                'contact_email': project.contact_email,
                'created_at': project.metadata.created_at.isoformat() if project.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'project'])} projects")

        # 11. Load Publications
        print("📚 Loading Publications...")
        publications = Publication.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {publications.count()} publications")

        for publication in publications:
            combined_text = f"{publication.metadata.title} {publication.metadata.description} {publication.authors} {publication.publisher}"

            knowledge_item = {
                'id': f"publication_{publication.id}",
                'actual_id': publication.id,
                'title': publication.metadata.title,
                'description': f"{publication.metadata.description} Authors: {publication.authors}",
                'type': 'publication',
                'slug': publication.slug,
                'url': f'/cmis/knowledge-resources/publications/{publication.slug}/',
                'authors': publication.authors,
                'publisher': publication.publisher,
                'publication_date': publication.publication_date.strftime('%Y-%m-%d'),
                'publication_type': publication.publication_type,
                'doi': publication.doi,
                'isbn': publication.isbn,
                'created_at': publication.metadata.created_at.isoformat() if publication.metadata.created_at else None,
                'raw_text': combined_text
            }      
                 
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'publication'])} publications")

        # 12. Load Technologies
        print("🔬 Loading Technologies...")
        technologies = Technology.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {technologies.count()} technologies")

        for technology in technologies:
            combined_text = f"{technology.metadata.title} {technology.metadata.description} {technology.developer}"

            knowledge_item = {
                'id': f"technology_{technology.id}",
                'actual_id': technology.id,
                'title': technology.metadata.title,
                'description': f"{technology.metadata.description} Developer: {technology.developer}",
                'type': 'technology',
                'slug': technology.slug,
                'url': f'/cmis/knowledge-resources/technologies/{technology.slug}/',
                'developer': technology.developer,
                'release_date': technology.release_date.strftime('%Y-%m-%d') if technology.release_date else None,
                'patent_number': technology.patent_number,
                'license_type': technology.license_type,
                'created_at': technology.metadata.created_at.isoformat() if technology.metadata.created_at else None,
                'raw_text': combined_text
            }    

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'technology'])} technologies")
        
        # 13. Load Training/Seminars
        print("🎓 Loading Training/Seminars...")
        trainings = TrainingSeminar.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {trainings.count()} training/seminar items")

        for training in trainings:
            combined_text = f"{training.metadata.title} {training.metadata.description} {training.trainers} {training.target_audience}"

            knowledge_item = {
                'id': f"training_{training.id}",
                'actual_id': training.id,
                'title': training.metadata.title,
                'description': f"{training.metadata.description} Target: {training.target_audience}",
                'type': 'training',
                'slug': training.slug,
                'url': f'/cmis/knowledge-resources/trainings/{training.slug}/',
                'location': training.location,
                'trainers': training.trainers,
                'target_audience': training.target_audience,
                'start_date': training.start_date.strftime('%Y-%m-%d %H:%M'),
                'end_date': training.end_date.strftime('%Y-%m-%d %H:%M'),
                'created_at': training.metadata.created_at.isoformat() if training.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'training'])} training/seminars")

        # 14. Load Webinars
        print("💻 Loading Webinars...")
        webinars = Webinar.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {webinars.count()} webinars")

        for webinar in webinars:
            combined_text = f"{webinar.metadata.title} {webinar.metadata.description} {webinar.presenters} {webinar.platform}"

            knowledge_item = {
                'id': f"webinar_{webinar.id}",
                'actual_id': webinar.id,
                'title': webinar.metadata.title,
                'description': f"{webinar.metadata.description} Platform: {webinar.platform}",
                'type': 'webinar',
                'slug': webinar.slug,
                'url': f'/cmis/knowledge-resources/webinars/{webinar.slug}/',
                'webinar_date': webinar.webinar_date.strftime('%Y-%m-%d %H:%M'),
                'duration_minutes': webinar.duration_minutes,
                'platform': webinar.platform,
                'presenters': webinar.presenters,
                'created_at': webinar.metadata.created_at.isoformat() if webinar.metadata.created_at else None,
                'raw_text': combined_text
            }

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'webinar'])} webinars")

        # 15. Load Products
        print("🛒 Loading Products...")
        products = Product.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {products.count()} products")

        for product in products:
            combined_text = f"{product.metadata.title} {product.metadata.description} {product.manufacturer} {product.features}"

            knowledge_item = {
                'id': f"product_{product.id}",
                'actual_id': product.id,
                'title': product.metadata.title,
                'description': f"{product.metadata.description} Manufacturer: {product.manufacturer}",
                'type': 'product',
                'slug': product.slug,
                'url': f'/cmis/knowledge-resources/products/{product.slug}/',
                'manufacturer': product.manufacturer,
                'features': product.features,
                'technical_specifications': product.technical_specifications,
                'price': float(product.price) if product.price else None,
                'created_at': product.metadata.created_at.isoformat() if product.metadata.created_at else None,
                'raw_text': combined_text
            }
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'product'])} products")

        # 16. Load Forum Discussions
        print("💬 Loading Forum discussions...")
        forums = Forum.objects.select_related('author').all()
        print(f"Found {forums.count()} forum discussions")

        for forum in forums:
            try:
                author_name = 'Anonymous'
                if hasattr(forum, 'author') and forum.author:
                    author_name = f"{forum.author.first_name} {forum.author.last_name}".strip()
                    if not author_name.strip():
                        author_name = forum.author.username
                
                forum_commodities = [commodity.commodity_name for commodity in forum.commodity_id.all()]
                combined_text = f"{forum.forum_title} {forum.forum_question} {' '.join(forum_commodities)}"

                knowledge_item = {
                    'id': f"forum_{forum.forum_id}",
                    'actual_id': forum.forum_id,
                    'title': forum.forum_title,
                    'description': forum.forum_question,
                    'type': 'forum',
                    'slug': forum.slug,
                    'url': f'/cmis/forum/{forum.slug}/',
                    'author': author_name,
                    'commodities': forum_commodities,
                    'date_posted': forum.date_posted.strftime('%Y-%m-%d') if forum.date_posted else None,
                    'total_likes': forum.total_likes(),
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)
                
            except Exception as e:
                print(f"⚠️ Error processing forum {forum.forum_id}: {e}")
                continue

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'forum'])} forum discussions")

        # 17. Load CMI Data
        print("🏢 Loading CMI entries...")
        cmis = CMI.objects.filter(status='active')
        print(f"Found {cmis.count()} CMI entries")

        for cmi in cmis:
            combined_text = f"{cmi.cmi_name} {cmi.cmi_meaning} {cmi.cmi_description} {cmi.address}"

            knowledge_item = {
                'id': f"cmi_{cmi.cmi_id}",
                'actual_id': cmi.cmi_id,
                'title': cmi.cmi_name,
                'description': f"{cmi.cmi_meaning}. {cmi.cmi_description}",
                'type': 'cmi',
                'slug': cmi.slug,
                'cmi_meaning': cmi.cmi_meaning,
                'address': cmi.address,
                'contact_num': cmi.contact_num,
                'email': cmi.email,
                'url': f'/cmis/about-km/',
                'latitude': float(cmi.latitude) if cmi.latitude else None,
                'longitude': float(cmi.longitude) if cmi.longitude else None,
                'date_joined': cmi.date_joined.strftime('%Y-%m-%d') if cmi.date_joined else None,
                'website_url': cmi.url,
                'created_at': cmi.date_created.strftime('%Y-%m-%d') if cmi.date_created else None,
                'raw_text': combined_text
            }
        
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'cmi'])} CMI entries")

        # 18. Load FAQ Data - FIXED with correct field names
        print("❓ Loading FAQs...")
        try:
            faqs = FAQ.objects.filter(is_active=True).select_related('created_by')
            print(f"Found {faqs.count()} FAQs")

            for faq in faqs:
                try:
                    # Get creator name safely
                    creator_name = 'Anonymous'
                    if hasattr(faq, 'created_by') and faq.created_by:
                        creator_name = f"{faq.created_by.first_name} {faq.created_by.last_name}".strip()
                        if not creator_name.strip():
                            creator_name = faq.created_by.username
                    
                    combined_text = f"{faq.question} {faq.answer}"

                    knowledge_item = {
                        'id': f"faq_{faq.faq_id}",
                        'actual_id': faq.faq_id,
                        'title': faq.question,  
                        'description': faq.answer,  
                        'question': faq.question,  
                        'answer': faq.answer,      
                        'type': 'faq',
                        'slug': faq.slug,
                        'url': f'/cmis/faqs/', 
                        'created_by': creator_name,
                        'created_at': faq.created_at.strftime('%Y-%m-%d') if faq.created_at else None,
                        'total_reactions': faq.total_reactions(),
                        'anonymous_reactions': faq.anonymous_reactions,
                        'is_active': faq.is_active,
                        'raw_text': combined_text
                    }

                    knowledge_data.append(knowledge_item)
                    document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"⚠️ Error processing FAQ {faq.faq_id}: {e}")
                    continue

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'faq'])} FAQs")
            
        except Exception as e:
            print(f"⚠️ Error loading FAQs: {e}")

            # 19. Load About Rationales
            print("💡 Loading About Rationales...")
            rationales = AboutRationale.objects.all()
            print(f"Found {rationales.count()} rationales")

            for rationale in rationales:
                combined_text = f"{rationale.title} {rationale.detail}"

                knowledge_item = {
                    'id': f"rationale_{rationale.rationale_id}",
                    'actual_id': rationale.rationale_id,
                    'title': rationale.title,
                    'description': rationale.detail,
                    'type': 'rationale',
                    'about_id': rationale.about.about_id,
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'rationale'])} rationales")

            # 20. Load About Objectives
            print("🎯 Loading About Objectives...")
            objectives = AboutObjective.objects.prefetch_related('details').all()
            print(f"Found {objectives.count()} objectives")

            for objective in objectives:
                combined_text = f"{objective.title} {' '.join([detail.detail for detail in objective.details.all()])}"

                knowledge_item = {
                    'id': f"objective_{objective.objective_id}",
                    'actual_id': objective.objective_id,
                    'title': objective.title,
                    'description': combined_text,
                    'type': 'objective',
                    'about_id': objective.about.about_id,
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'objective'])} objectives")

            # 21. Load About Activities
            print("📋 Loading About Activities...")
            activities = AboutActivity.objects.all()
            print(f"Found {activities.count()} activities")

            for activity in activities:
                combined_text = f"{activity.title} {activity.detail}"

                knowledge_item = {
                    'id': f"activity_{activity.activity_id}",
                    'actual_id': activity.activity_id,
                    'title': activity.title,
                    'description': activity.detail,
                    'type': 'activity',
                    'about_id': activity.about.about_id,
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'activity'])} activities")

            # 22. Load About Timelines
            print("📅 Loading About Timelines...")
            timelines = AboutTimeline.objects.prefetch_related('bullets', 'images').all()
            print(f"Found {timelines.count()} timelines")

            for timeline in timelines:
                combined_text = f"{timeline.title} {timeline.description} {' '.join([bullet.details for bullet in timeline.bullets.all()])}"

                knowledge_item = {
                    'id': f"timeline_{timeline.timeline_id}",
                    'actual_id': timeline.timeline_id,
                    'title': timeline.title,
                    'description': timeline.description,
                    'type': 'timeline',
                    'about_id': timeline.about.about_id,
                    'start_date': timeline.date_start.strftime('%Y-%m-%d') if timeline.date_start else None,
                    'end_date': timeline.date_end.strftime('%Y-%m-%d') if timeline.date_end else None,
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'timeline'])} timelines")

            # 23. Load About Team Members
            print("👥 Loading About Team Members...")
            team_members = AboutTeamMember.objects.prefetch_related('socials').all()
            print(f"Found {team_members.count()} team members")

            for member in team_members:
                combined_text = f"{member.first_name} {member.last_name} {member.role} {member.description}"

                knowledge_item = {
                    'id': f"team_member_{member.member_id}",
                    'actual_id': member.member_id,
                    'name': f"{member.first_name} {member.last_name}".strip(),
                    'role': member.role,
                    'description': member.description,
                    'type': 'team_member',
                    'about_id': member.about.about_id,
                    'social_links': [{'platform': social.platform, 'link': social.link} for social in member.socials.all()],
                    'raw_text': combined_text
                }

                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)

            print(f"✅ Loaded {len([item for item in knowledge_data if item['type'] == 'team_member'])} team members")

        print(f"🎉 Successfully loaded {len(knowledge_data)} total items into knowledge base")
        
        type_counts = {}
        for item in knowledge_data:
            item_type = item.get('type', 'unknown')
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        print("📊 Summary by type:")
        for item_type, count in sorted(type_counts.items()):
            print(f"   • {item_type}: {count}")

        return knowledge_data, document_texts
        
    except Exception as e:
        logger.error(f"Error loading knowledge base from database: {e}")
        print(f"❌ Error loading from database: {e}")
        import traceback
        print(traceback.format_exc())
        return [], []

def get_database_statistics():
    """Get statistics about the database content for reporting"""
    try:
        from appAdmin.models import ResourceMetadata, KnowledgeResources
        from appCmi.models import Forum, FAQ
        
        stats = {
            'resources': 0,
            'knowledge_resources': 0,
            'forums': 0,
            'faqs': 0,
            'total_approved': 0,
            'last_updated': None,
            'errors': []
        }
        
        # Count ResourceMetadata
        try:
            stats['resources'] = ResourceMetadata.objects.filter(is_approved=True).count()
        except Exception as e:
            stats['errors'].append(f"ResourceMetadata: {e}")
        
        # Count KnowledgeResources
        try:
            stats['knowledge_resources'] = KnowledgeResources.objects.filter(status='active').count()
        except Exception as e:
            stats['errors'].append(f"KnowledgeResources: {e}")
        
        # Count Forums
        try:
            stats['forums'] = Forum.objects.count()
        except Exception as e:
            stats['errors'].append(f"Forum: {e}")
        
        # Count FAQs
        try:
            stats['faqs'] = FAQ.objects.filter(is_active=True).count()
        except Exception as e:
            stats['errors'].append(f"FAQ: {e}")
        
        # Get last updated timestamp
        try:
            latest_resource = ResourceMetadata.objects.filter(
                is_approved=True
            ).order_by('-created_at').first()
            
            if latest_resource and latest_resource.created_at:
                stats['last_updated'] = latest_resource.created_at.isoformat()
        except Exception as e:
            stats['errors'].append(f"Last updated: {e}")
        
        stats['total_approved'] = sum([
            stats['resources'],
            stats['knowledge_resources'],
            stats['forums'], 
            stats['faqs']
        ])
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return {'error': str(e)}

def validate_database_connection():
    """Validate that we can connect to database and required models exist"""
    try:
        from django.db import connection
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test model imports
        from appAdmin.models import ResourceMetadata, KnowledgeResources, About
        from appCmi.models import Forum, FAQ
        
        # Test basic model access
        ResourceMetadata.objects.count()
        KnowledgeResources.objects.count()
        Forum.objects.count()
        FAQ.objects.count()
        About.objects.count()
        
        return True, "Database connection and models are accessible"
        
    except Exception as e:
        return False, f"Database validation failed: {e}"