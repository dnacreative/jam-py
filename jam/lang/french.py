# -*- coding: utf-8 -*-

dictionary = \
{
    'lang':                             u'fr',
#admin fields
    'admin':                            u'Administrateur',
    'catalogs':                         u'Catalogues',
    'journals':                         u'Journaux',
    'tables':                           u'Tables',
    'reports':                          u'Rapport',
    'details':                          u'Détails',
    'id':                               u'N°Enregistrement',
    'deleted_flag':                     u'Indicateur de supression',
    'caption':                          u'Intitulé',
    'name':                             u'Nom',
    'table_name':                       u'Table',
    'template':                         u'Modèle de rapport',
    'report_module':                    u'Module de rapport',
    'params_template':                  u'Params IU',
    'view_template':                    u'Modèle de rapport',
    'visible':                          u'Visible',
    'client_module':                    u'Module client',
    'web_client_module':                u'Module webClient ',
    'server_module':                    u'Module Serveur',
    'report_module':                    u'Module de rapport',
    'project':                          u'Projet',
    'users':                            u'Utilisateur',
    'roles':                            u'Rôles',
    'privileges':                       u'Privilèges',
    'tasks':                            u'Tache',
    'safe_mode':                        u'Mode protégé',
    'language':                         u'Langage',
    'author':                           u'Auteur',
    'interface':                        u'Interface',
    'db_type':                          u'type BD',
    'db_name':                          u'Nom de la base',
    'alias':                            u'Base de données',
    'data_type':                        u'Type',
    'filter_type':                      u'Type de filtre',
    'size':                             u'Taille',
    'object':                           u'Item à rechercher',
    'object_field':                     u'Champ de recherche',
    'master_field':                     u'Champ maître',
    'required':                         u'Obligatoire',
    'calculated':                       u'Calc.',
    'default':                          u'Défaut',
    'read_only':                        u'Lecture seule',
    'alignment':                        u'Align.',
    'active':                           u'Activé',
    'date':                             u'Date',
    'role':                             u'Rôle',
    'info':                             u'Information',
    'item':                             u'Item',
    'can_view':                         u'Peut voir',
    'can_create':                       u'Peut créer',
    'can_edit':                         u'Peut modifier',
    'can_delete':                       u'Peut supprimer',
    'fields':                           u'Champs',
    'field':                            u'Champ',
    'filter':                           u'Filtre',
    'filters':                          u'Filtres',
    'index':                            u'Index',
    'index_name':                       u"Nom de l'index",
    'report_params':                    u'Params du Rapport',
    'error':                            u'Erreur',
#admin interface
    'db':                               u'Base de données',
    'export':                           u'Export',
    'import':                           u'Import',
    'viewing':                          u'Affichage',
    'editing':                          u'Edition',
    'filters':                          u'Filtres',
    'order':                            u'Ordre',
    'indices':                          u'Indices',
    'foreign_keys':                     u'clés étrangères',
    'select_all':                       u'Select. tout',
    'unselect_all':                     u'Déselect. tout',
    'project_params':                   u'Paramètres du projet',
    'project_locale':                   u'Param.locaux du projet',
    'reserved_word':                    u'Le nom est un mot réservé',
#editor
    'case_sensitive':                   u'Sensible à la casse',
    'whole_words':                      u'Chercher le mots entiers',
    'in_task':                          u'Dans la tâche',
    'text_not_found':                   u'Texte non trouvé.\nModifiez et chercher à nouveau ?',
    'text_changed':                     u'Le module a été changé.\nSauver avant de fermer?',
    'go_to_line':                       u'Aller à la ligne',
    'go_to':                            u'Aller à',
    'line':                             u'Ligne',
#admin editors
    'caption_name':                     u'Nom',
    'caption_word_wrap':                u'Wrap',
    'caption_expand':                   u'Exp.',
    'caption_edit':                     u'Edit',
    'caption_descening':                u'Desc.',
#admin messages
    'fill_task_attrubutes':             u'Fill in the caption, name and database type attributes.',
    'can_not_connect':                  u"Impossible de se connecter à la base %s",
    'field_used_in_filters':            u"Impossible de supprimer le champ %s.\n utilisé dans la définition du filtre:\n%s",
    'field_used_in_fields':             u"Impossible de supprimer le champ %s.\n Utilisé dans la définition du champ:\n%s",
    'field_used_in_indices':            u"Impossible de supprimer le champ %s.\n Utilisé dans la définition d'un index:\n%s",
    'field_is_system':                  u"Impossible de supprimer un champ systeme..",
    'detail_mess':                      u'%s - détail %s',
    'item_used_in_items':               u"Impossibe de supprimer l'item %s.\n Utilisé dans la définition de l'item:\n%s",
    'field_mess':                       u'%s - champ %s',
    'item_used_in_fields':              u"Impossibe de supprimer l'item %s.\n Utilisé dans la définition du champ:\n%s",
    'param_mess':                       u'%s - parametre %s',
    'item_used_in_params':              u"Impossible de supprimer l'item %s.\n Est utilisé dans le paramètre :\n%s",
    'invalid_name':                     u'Nom incorrect.',
    'invalid_field_name':               u'Nom de champ incorrect.',
    'type_is_required':                 u'Type de champ obligatoire.',
    'index_name_required':              u"Nom de l'index obligatoire.",
    'index_fields_required':            u"Les champs de l'index sont obligatoire.",
    'cant_delete_group':                u"Impossible de supprimer un groupe",
    'object_field_required':            u'Un champ item est obligatoire.',
    'no_tasks_ptoject':                 u"Il n'y a pas de tâches dans le projet.",
    'stop_server':                      u'Arrêter le serveur.',
#interface buttons and labels
    'yes':                              u'Oui',
    'no':                               u'Non',
    'ok':                               u'OK',
    'cancel':                           u'Annuler',
    'delete':                           u'Supprimer',
    'new':                              u'Nouveau',
    'edit':                             u'Editer',
    'copy':                             u'Copier',
    'print':                            u'Imprimer',
    'save':                             u'Sauvegarder',
    'open':                             u'Ouvrir',
    'close':                            u'Fermer',
    'select':                           u'Selectionner',
    'filter':                           u'Filtrer',
    'apply':                            u'Appliquer',
    'find':                             u'Chercher',
    'replace':                          u'Remplacer',
    'view':                             u'Afficher',
    'log_in':                           u'Se connecter',
    'login':                            u'Connexion',
    'password':                         u'Mot de passe',
    'log_out':                          u'Se déconnecter',
#runtime messages
    'invalid_int':                      u'%s valeur incorrecte - doit être un integer',
    'invalid_float':                    u'%s valeur incorrecte - doit être un float',
    'invalid_cur':                      u'%s valeur incorrecte - doit être de type monnaie',
    'invalid_date':                     u'%s valeur incorrecte - doit être une date',
    'invalid_bool':                     u'%s valeur incorrecte - doit être un boolean',
    'invalid_value':                    u'%s valeur incorrecte',
    'value_required':                   u'Une valeur est obligatoire',
    'invalid_length':                   u'Taille du texte supérieure à la taille maximum - %d',
    'save_changes':                     u'Les données ont changé. Voulez-vous les sauvegarder ?',
    'apply_changes':                    u"Les modifications des données n'ont pas été soumises au serveur. Voulez-vous soumettre ces modifications ?",
    'delete_record':                    u"Supprimer l'enregistrement ?",
    'server_request_error':             u'Erreur dans la requête au serveur',
    'cant_delete_used_record':          u"Impossible de supprimer l'enregistrement. Il est en cours d'utilisation.",
    'website_maintenance':              u"Le site web est actuellement en maintenance.",
    'items_selected':                   u"sélectionné: %d",
#rights messages
    'cant_view':                        u"%s: Vous n'êtes pas autorisés à afficher",
    'cant_create':                      u"%s: Vous n'êtes pas autosisés à créer" ,
    'cant_edit':                        u"%s: Vous n'êtes pas autosisés à editer",
    'cant_delete':                      u"%s: Vous n'êtes pas autosisés à supprimer",
#calendar
    'week_start':                        0,
    'days_min':                         [u'Di', u'Lu', u'Ma', u'Me', u'Je', u'Ve', u'Sa', u'Su'],
    'months':                           [u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Decembre'],
    'months_short':                     [u'Jan', u'Fév', u'Mar', u'Avr', u'Mai', u'Jui', u'Jul', u'Aoû', u'Sep', u'Oct', u'Nov', u'Déc'],
#grid
    'page':                             u'Page',
    'of':                               u'de'
}
