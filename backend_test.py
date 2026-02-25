#!/usr/bin/env python3
"""
Tests complets pour l'API ZLECAf - Système Commercial Africain
Tests tous les endpoints avec données réelles et vérifications complètes
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration de l'API
BASE_URL = "https://inspiring-proskuriakova-1.preview.emergentagent.com/api"
TIMEOUT = 30

class ZLECAfAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ZLECAf-API-Tester/1.0'
        })
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Enregistrer le résultat d'un test"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")
    
    def test_api_root(self):
        """Test GET /api/ - Point d'entrée de l'API"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'ZLECAf' in data['message']:
                    self.log_result(
                        "API Root Endpoint", 
                        True, 
                        "Point d'entrée accessible avec message ZLECAf",
                        {'response': data}
                    )
                else:
                    self.log_result(
                        "API Root Endpoint", 
                        False, 
                        "Réponse ne contient pas le message ZLECAf attendu",
                        {'response': data}
                    )
            else:
                self.log_result(
                    "API Root Endpoint", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code, 'response': response.text}
                )
                
        except Exception as e:
            self.log_result(
                "API Root Endpoint", 
                False, 
                f"Erreur de connexion: {str(e)}",
                {'error': str(e)}
            )
    
    def test_countries_list(self):
        """Test GET /api/countries - Liste des 54 pays membres ZLECAf"""
        try:
            response = self.session.get(f"{self.base_url}/countries", timeout=TIMEOUT)
            
            if response.status_code == 200:
                countries = response.json()
                
                # Vérifier que c'est une liste
                if not isinstance(countries, list):
                    self.log_result(
                        "Countries List", 
                        False, 
                        "La réponse n'est pas une liste",
                        {'response_type': type(countries).__name__}
                    )
                    return
                
                # Vérifier le nombre de pays (54 membres ZLECAf)
                if len(countries) != 54:
                    self.log_result(
                        "Countries List", 
                        False, 
                        f"Nombre de pays incorrect: {len(countries)} au lieu de 54",
                        {'count': len(countries)}
                    )
                    return
                
                # Vérifier la structure des données
                required_fields = ['code', 'name', 'region', 'iso3', 'wb_code', 'population']
                sample_country = countries[0]
                missing_fields = [field for field in required_fields if field not in sample_country]
                
                if missing_fields:
                    self.log_result(
                        "Countries List", 
                        False, 
                        f"Champs manquants dans les données pays: {missing_fields}",
                        {'sample_country': sample_country}
                    )
                    return
                
                # Vérifier des pays spécifiques
                country_codes = [country['code'] for country in countries]
                expected_countries = ['NG', 'MA', 'MU', 'ZA', 'EG', 'KE']
                missing_countries = [code for code in expected_countries if code not in country_codes]
                
                if missing_countries:
                    self.log_result(
                        "Countries List", 
                        False, 
                        f"Pays importants manquants: {missing_countries}",
                        {'missing': missing_countries}
                    )
                    return
                
                self.log_result(
                    "Countries List", 
                    True, 
                    f"Liste complète de {len(countries)} pays avec structure correcte",
                    {'sample_countries': countries[:3]}
                )
                
            else:
                self.log_result(
                    "Countries List", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Countries List", 
                False, 
                f"Erreur lors de la récupération des pays: {str(e)}",
                {'error': str(e)}
            )
    
    def test_country_profiles(self):
        """Test GET /api/country-profile/{country_code} - Profils économiques avec nouvelles données"""
        # Tests spécifiques avec nouvelles données validées
        test_countries_data = {
            'NG': {'expected_gdp': 374.984, 'expected_pop': 227883000, 'name': 'Nigéria'},
            'DZ': {'expected_gdp': 269.128, 'expected_pop': 46700000, 'name': 'Algérie'},
            'ZA': {'expected_gdp': 377.782, 'expected_pop': 63212000, 'name': 'Afrique du Sud'},
            'EG': {'expected_gdp': 331.59, 'expected_pop': 114536000, 'name': 'Égypte'}
        }
        
        for country_code, expected_data in test_countries_data.items():
            try:
                response = self.session.get(f"{self.base_url}/country-profile/{country_code}", timeout=TIMEOUT)
                
                if response.status_code == 200:
                    profile = response.json()
                    
                    # Vérifier les champs obligatoires
                    required_fields = ['country_code', 'country_name', 'region', 'projections']
                    missing_fields = [field for field in required_fields if field not in profile]
                    
                    if missing_fields:
                        self.log_result(
                            f"Country Profile {country_code}", 
                            False, 
                            f"Champs manquants: {missing_fields}",
                            {'profile': profile}
                        )
                        continue
                    
                    # Vérifier les données économiques spécifiques
                    gdp_check = profile.get('gdp_usd') == expected_data['expected_gdp']
                    pop_check = profile.get('population') == expected_data['expected_pop']
                    name_check = profile.get('country_name') == expected_data['name']
                    
                    if not gdp_check:
                        self.log_result(
                            f"Country Profile {country_code}", 
                            False, 
                            f"PIB incorrect: {profile.get('gdp_usd')} au lieu de {expected_data['expected_gdp']}",
                            {'actual_gdp': profile.get('gdp_usd'), 'expected_gdp': expected_data['expected_gdp']}
                        )
                        continue
                    
                    if not pop_check:
                        self.log_result(
                            f"Country Profile {country_code}", 
                            False, 
                            f"Population incorrecte: {profile.get('population')} au lieu de {expected_data['expected_pop']}",
                            {'actual_pop': profile.get('population'), 'expected_pop': expected_data['expected_pop']}
                        )
                        continue
                    
                    # Vérifier les projections
                    if 'projections' not in profile or not isinstance(profile['projections'], dict):
                        self.log_result(
                            f"Country Profile {country_code}", 
                            False, 
                            "Projections manquantes ou format incorrect",
                            {'projections': profile.get('projections')}
                        )
                        continue
                    
                    # Vérifier les données ZLECAf
                    projections = profile['projections']
                    zlecaf_fields = ['zlecaf_potential_level', 'zlecaf_opportunities']
                    has_zlecaf_data = any(field in projections for field in zlecaf_fields)
                    
                    if not has_zlecaf_data:
                        self.log_result(
                            f"Country Profile {country_code}", 
                            False, 
                            "Données ZLECAf manquantes dans les projections",
                            {'projections': projections}
                        )
                        continue
                    
                    self.log_result(
                        f"Country Profile {country_code}", 
                        True, 
                        f"Profil validé avec nouvelles données - {expected_data['name']}: PIB {expected_data['expected_gdp']}Mds, Pop {expected_data['expected_pop']}M",
                        {
                            'country': profile['country_name'],
                            'gdp': profile.get('gdp_usd'),
                            'population': profile.get('population'),
                            'zlecaf_level': projections.get('zlecaf_potential_level')
                        }
                    )
                    
                elif response.status_code == 404:
                    self.log_result(
                        f"Country Profile {country_code}", 
                        False, 
                        f"Pays {country_code} non trouvé",
                        {'status_code': response.status_code}
                    )
                else:
                    self.log_result(
                        f"Country Profile {country_code}", 
                        False, 
                        f"Code de statut incorrect: {response.status_code}",
                        {'status_code': response.status_code}
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Country Profile {country_code}", 
                    False, 
                    f"Erreur lors de la récupération du profil: {str(e)}",
                    {'error': str(e)}
                )
    
    def test_rules_of_origin(self):
        """Test GET /api/rules-of-origin/{hs_code} - Règles d'origine"""
        test_codes = ['010121', '847989']
        
        for hs_code in test_codes:
            try:
                response = self.session.get(f"{self.base_url}/rules-of-origin/{hs_code}", timeout=TIMEOUT)
                
                if response.status_code == 200:
                    rules = response.json()
                    
                    # Vérifier les champs obligatoires
                    required_fields = ['hs_code', 'sector_code', 'rules', 'explanation']
                    missing_fields = [field for field in required_fields if field not in rules]
                    
                    if missing_fields:
                        self.log_result(
                            f"Rules of Origin {hs_code}", 
                            False, 
                            f"Champs manquants: {missing_fields}",
                            {'rules': rules}
                        )
                        continue
                    
                    # Vérifier la structure des règles
                    rules_data = rules['rules']
                    required_rule_fields = ['rule', 'requirement', 'regional_content']
                    missing_rule_fields = [field for field in required_rule_fields if field not in rules_data]
                    
                    if missing_rule_fields:
                        self.log_result(
                            f"Rules of Origin {hs_code}", 
                            False, 
                            f"Champs manquants dans les règles: {missing_rule_fields}",
                            {'rules_data': rules_data}
                        )
                        continue
                    
                    # Vérifier l'explication
                    explanation = rules['explanation']
                    required_explanation_fields = ['rule_type', 'requirement', 'regional_content_minimum', 'documentation_required']
                    missing_explanation_fields = [field for field in required_explanation_fields if field not in explanation]
                    
                    if missing_explanation_fields:
                        self.log_result(
                            f"Rules of Origin {hs_code}", 
                            False, 
                            f"Champs manquants dans l'explication: {missing_explanation_fields}",
                            {'explanation': explanation}
                        )
                        continue
                    
                    # Vérifier la cohérence des données
                    if rules['hs_code'] != hs_code:
                        self.log_result(
                            f"Rules of Origin {hs_code}", 
                            False, 
                            f"Code SH incohérent: {rules['hs_code']} != {hs_code}",
                            {'returned_code': rules['hs_code']}
                        )
                        continue
                    
                    self.log_result(
                        f"Rules of Origin {hs_code}", 
                        True, 
                        f"Règles d'origine complètes pour {hs_code} - {rules_data['rule']}",
                        {
                            'rule_type': rules_data['rule'],
                            'regional_content': rules_data['regional_content'],
                            'requirement': rules_data['requirement']
                        }
                    )
                    
                elif response.status_code == 404:
                    self.log_result(
                        f"Rules of Origin {hs_code}", 
                        False, 
                        f"Règles non trouvées pour le code SH {hs_code}",
                        {'status_code': response.status_code}
                    )
                else:
                    self.log_result(
                        f"Rules of Origin {hs_code}", 
                        False, 
                        f"Code de statut incorrect: {response.status_code}",
                        {'status_code': response.status_code}
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Rules of Origin {hs_code}", 
                    False, 
                    f"Erreur lors de la récupération des règles: {str(e)}",
                    {'error': str(e)}
                )
    
    def test_tax_implementation_senegal_cote_ivoire(self):
        """Test spécifique de l'implémentation des taxes SN->CI selon la demande"""
        # Payload de test spécifique de la demande de révision
        test_payload = {
            "origin_country": "SN",  # Sénégal - pays CEDEAO
            "destination_country": "CI",  # Côte d'Ivoire - pays CEDEAO/UEMOA
            "hs_code": "010121",
            "value": 100000
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/calculate-tariff", 
                json=test_payload, 
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                calculation = response.json()
                
                # Vérifier les champs de taxes requis
                required_tax_fields = [
                    'normal_vat_amount', 'normal_vat_rate',
                    'normal_statistical_fee', 'normal_community_levy', 'normal_ecowas_levy',
                    'normal_total_cost', 'zlecaf_total_cost',
                    'total_savings_with_taxes', 'total_savings_percentage'
                ]
                missing_fields = [field for field in required_tax_fields if field not in calculation]
                
                if missing_fields:
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        f"Champs de taxes manquants: {missing_fields}",
                        {'calculation': calculation}
                    )
                    return
                
                # Vérifier les taux spécifiques pour la Côte d'Ivoire
                expected_vat_rate = 18.0  # TVA Côte d'Ivoire = 18%
                expected_statistical_fee_rate = 1.0  # Redevance statistique = 1%
                expected_community_levy_rate = 0.5  # Prélèvement communautaire = 0.5%
                expected_ecowas_levy_rate = 1.0  # Prélèvement CEDEAO = 1%
                
                if calculation['normal_vat_rate'] != expected_vat_rate:
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        f"Taux TVA incorrect: {calculation['normal_vat_rate']}% au lieu de {expected_vat_rate}%",
                        {'actual_vat_rate': calculation['normal_vat_rate']}
                    )
                    return
                
                # Vérifier la formule de calcul de la TVA
                # Base TVA = Valeur + DD + autres taxes
                value = calculation['value']
                customs_duty = calculation['normal_tariff_amount']
                statistical_fee = calculation['normal_statistical_fee']
                community_levy = calculation['normal_community_levy']
                ecowas_levy = calculation['normal_ecowas_levy']
                
                expected_vat_base = value + customs_duty + statistical_fee + community_levy + ecowas_levy
                expected_vat_amount = expected_vat_base * (expected_vat_rate / 100)
                
                # Vérifier les calculs avec une tolérance de 0.01
                if abs(calculation['normal_vat_amount'] - expected_vat_amount) > 0.01:
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        f"Calcul TVA incorrect: {calculation['normal_vat_amount']:.2f} au lieu de {expected_vat_amount:.2f}",
                        {
                            'vat_base_calculated': expected_vat_base,
                            'vat_amount_calculated': expected_vat_amount,
                            'vat_amount_actual': calculation['normal_vat_amount']
                        }
                    )
                    return
                
                # Vérifier les autres taxes
                expected_statistical_fee = value * (expected_statistical_fee_rate / 100)
                expected_community_levy = value * (expected_community_levy_rate / 100)
                expected_ecowas_levy = value * (expected_ecowas_levy_rate / 100)
                
                tax_checks = [
                    abs(statistical_fee - expected_statistical_fee) < 0.01,
                    abs(community_levy - expected_community_levy) < 0.01,
                    abs(ecowas_levy - expected_ecowas_levy) < 0.01
                ]
                
                if not all(tax_checks):
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        "Erreurs dans le calcul des autres taxes",
                        {
                            'statistical_fee': {'actual': statistical_fee, 'expected': expected_statistical_fee},
                            'community_levy': {'actual': community_levy, 'expected': expected_community_levy},
                            'ecowas_levy': {'actual': ecowas_levy, 'expected': expected_ecowas_levy}
                        }
                    )
                    return
                
                # Vérifier le total normal
                expected_normal_total = value + customs_duty + calculation['normal_vat_amount'] + statistical_fee + community_levy + ecowas_levy
                
                if abs(calculation['normal_total_cost'] - expected_normal_total) > 0.01:
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        f"Total normal incorrect: {calculation['normal_total_cost']:.2f} au lieu de {expected_normal_total:.2f}",
                        {
                            'normal_total_calculated': expected_normal_total,
                            'normal_total_actual': calculation['normal_total_cost']
                        }
                    )
                    return
                
                # Vérifier les économies totales avec taxes
                expected_total_savings = calculation['normal_total_cost'] - calculation['zlecaf_total_cost']
                expected_savings_percentage = (expected_total_savings / calculation['normal_total_cost']) * 100
                
                if abs(calculation['total_savings_with_taxes'] - expected_total_savings) > 0.01:
                    self.log_result(
                        "Tax Implementation SN->CI", 
                        False, 
                        f"Économies totales incorrectes: {calculation['total_savings_with_taxes']:.2f} au lieu de {expected_total_savings:.2f}",
                        {
                            'total_savings_calculated': expected_total_savings,
                            'total_savings_actual': calculation['total_savings_with_taxes']
                        }
                    )
                    return
                
                self.log_result(
                    "Tax Implementation SN->CI", 
                    True, 
                    f"✅ Implémentation des taxes validée - TVA: {calculation['normal_vat_rate']}%, Économies totales: {calculation['total_savings_with_taxes']:.2f} USD ({calculation['total_savings_percentage']:.1f}%)",
                    {
                        'vat_rate': f"{calculation['normal_vat_rate']}%",
                        'vat_amount': calculation['normal_vat_amount'],
                        'statistical_fee': statistical_fee,
                        'community_levy': community_levy,
                        'ecowas_levy': ecowas_levy,
                        'normal_total': calculation['normal_total_cost'],
                        'zlecaf_total': calculation['zlecaf_total_cost'],
                        'total_savings': calculation['total_savings_with_taxes'],
                        'savings_percentage': calculation['total_savings_percentage']
                    }
                )
                
            else:
                self.log_result(
                    "Tax Implementation SN->CI", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code, 'response': response.text}
                )
                
        except Exception as e:
            self.log_result(
                "Tax Implementation SN->CI", 
                False, 
                f"Erreur lors du test des taxes: {str(e)}",
                {'error': str(e), 'payload': test_payload}
            )

    def test_tariff_calculation(self):
        """Test POST /api/calculate-tariff - Calcul complet des tarifs avec nouvelles données"""
        # Payload de test spécifique mentionné dans la demande
        test_payload = {
            "origin_country": "NG",
            "destination_country": "EG",
            "hs_code": "010121",
            "value": 100000
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/calculate-tariff", 
                json=test_payload, 
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                calculation = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = [
                    'id', 'origin_country', 'destination_country', 'hs_code', 'value',
                    'normal_tariff_rate', 'normal_tariff_amount', 'zlecaf_tariff_rate', 
                    'zlecaf_tariff_amount', 'savings', 'savings_percentage', 'rules_of_origin'
                ]
                missing_fields = [field for field in required_fields if field not in calculation]
                
                if missing_fields:
                    self.log_result(
                        "Tariff Calculation", 
                        False, 
                        f"Champs manquants dans le calcul: {missing_fields}",
                        {'calculation': calculation}
                    )
                    return
                
                # Vérifier la cohérence des données d'entrée
                input_checks = [
                    calculation['origin_country'] == test_payload['origin_country'],
                    calculation['destination_country'] == test_payload['destination_country'],
                    calculation['hs_code'] == test_payload['hs_code'],
                    calculation['value'] == test_payload['value']
                ]
                
                if not all(input_checks):
                    self.log_result(
                        "Tariff Calculation", 
                        False, 
                        "Données d'entrée incohérentes dans la réponse",
                        {
                            'input': test_payload,
                            'output': {k: calculation[k] for k in ['origin_country', 'destination_country', 'hs_code', 'value']}
                        }
                    )
                    return
                
                # Vérifier la logique des calculs
                expected_normal_amount = calculation['value'] * calculation['normal_tariff_rate']
                expected_zlecaf_amount = calculation['value'] * calculation['zlecaf_tariff_rate']
                expected_savings = expected_normal_amount - expected_zlecaf_amount
                
                calculation_checks = [
                    abs(calculation['normal_tariff_amount'] - expected_normal_amount) < 0.01,
                    abs(calculation['zlecaf_tariff_amount'] - expected_zlecaf_amount) < 0.01,
                    abs(calculation['savings'] - expected_savings) < 0.01,
                    calculation['zlecaf_tariff_rate'] < calculation['normal_tariff_rate'],
                    calculation['savings'] > 0,
                    calculation['savings_percentage'] > 0
                ]
                
                if not all(calculation_checks):
                    self.log_result(
                        "Tariff Calculation", 
                        False, 
                        "Erreurs dans la logique de calcul des tarifs",
                        {
                            'normal_rate': calculation['normal_tariff_rate'],
                            'zlecaf_rate': calculation['zlecaf_tariff_rate'],
                            'normal_amount': calculation['normal_tariff_amount'],
                            'zlecaf_amount': calculation['zlecaf_tariff_amount'],
                            'savings': calculation['savings'],
                            'savings_percentage': calculation['savings_percentage']
                        }
                    )
                    return
                
                # Vérifier les règles d'origine
                if not isinstance(calculation['rules_of_origin'], dict):
                    self.log_result(
                        "Tariff Calculation", 
                        False, 
                        "Règles d'origine manquantes ou format incorrect",
                        {'rules_of_origin': calculation['rules_of_origin']}
                    )
                    return
                
                # Vérifier la présence d'un ID unique
                if not calculation['id'] or len(calculation['id']) < 10:
                    self.log_result(
                        "Tariff Calculation", 
                        False, 
                        "ID de calcul manquant ou invalide",
                        {'id': calculation['id']}
                    )
                    return
                
                self.log_result(
                    "Tariff Calculation", 
                    True, 
                    f"Calcul tarifaire réussi - Économies: {calculation['savings']:.2f} USD ({calculation['savings_percentage']:.1f}%)",
                    {
                        'normal_tariff': f"{calculation['normal_tariff_rate']*100:.1f}%",
                        'zlecaf_tariff': f"{calculation['zlecaf_tariff_rate']*100:.1f}%",
                        'savings_usd': calculation['savings'],
                        'savings_percent': calculation['savings_percentage'],
                        'calculation_id': calculation['id']
                    }
                )
                
            elif response.status_code == 400:
                self.log_result(
                    "Tariff Calculation", 
                    False, 
                    "Erreur de validation des données d'entrée",
                    {'status_code': response.status_code, 'response': response.text}
                )
            else:
                self.log_result(
                    "Tariff Calculation", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code, 'response': response.text}
                )
                
        except Exception as e:
            self.log_result(
                "Tariff Calculation", 
                False, 
                f"Erreur lors du calcul tarifaire: {str(e)}",
                {'error': str(e), 'payload': test_payload}
            )
    
    def test_statistics(self):
        """Test GET /api/statistics - Statistiques complètes ZLECAf"""
        try:
            response = self.session.get(f"{self.base_url}/statistics", timeout=TIMEOUT)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Vérifier les sections principales
                required_sections = ['overview', 'trade_statistics', 'zlecaf_impact', 'projections']
                missing_sections = [section for section in required_sections if section not in stats]
                
                if missing_sections:
                    self.log_result(
                        "Statistics", 
                        False, 
                        f"Sections manquantes: {missing_sections}",
                        {'stats': stats}
                    )
                    return
                
                # Vérifier la section overview
                overview = stats['overview']
                required_overview_fields = ['total_calculations', 'african_countries_members', 'combined_population', 'estimated_combined_gdp']
                missing_overview_fields = [field for field in required_overview_fields if field not in overview]
                
                if missing_overview_fields:
                    self.log_result(
                        "Statistics", 
                        False, 
                        f"Champs manquants dans overview: {missing_overview_fields}",
                        {'overview': overview}
                    )
                    return
                
                # Vérifier les valeurs logiques
                if overview['african_countries_members'] != 54:
                    self.log_result(
                        "Statistics", 
                        False, 
                        f"Nombre de pays membres incorrect: {overview['african_countries_members']} au lieu de 54",
                        {'members_count': overview['african_countries_members']}
                    )
                    return
                
                if overview['combined_population'] < 1000000000:  # Au moins 1 milliard
                    self.log_result(
                        "Statistics", 
                        False, 
                        f"Population combinée trop faible: {overview['combined_population']}",
                        {'population': overview['combined_population']}
                    )
                    return
                
                # Vérifier l'impact ZLECAf
                zlecaf_impact = stats['zlecaf_impact']
                required_impact_fields = ['average_tariff_reduction', 'estimated_trade_creation', 'job_creation_potential']
                missing_impact_fields = [field for field in required_impact_fields if field not in zlecaf_impact]
                
                if missing_impact_fields:
                    self.log_result(
                        "Statistics", 
                        False, 
                        f"Champs manquants dans zlecaf_impact: {missing_impact_fields}",
                        {'zlecaf_impact': zlecaf_impact}
                    )
                    return
                
                # Vérifier les projections
                projections = stats['projections']
                if '2025' not in projections or '2030' not in projections:
                    self.log_result(
                        "Statistics", 
                        False, 
                        "Projections 2025 et 2030 manquantes",
                        {'projections': projections}
                    )
                    return
                
                # Vérifier les sources de données
                if 'data_sources' not in stats or not isinstance(stats['data_sources'], list):
                    self.log_result(
                        "Statistics", 
                        False, 
                        "Sources de données manquantes ou format incorrect",
                        {'data_sources': stats.get('data_sources')}
                    )
                    return
                
                self.log_result(
                    "Statistics", 
                    True, 
                    f"Statistiques complètes - {overview['african_countries_members']} pays, {overview['total_calculations']} calculs",
                    {
                        'countries': overview['african_countries_members'],
                        'calculations': overview['total_calculations'],
                        'population': overview['combined_population'],
                        'gdp': overview['estimated_combined_gdp'],
                        'tariff_reduction': zlecaf_impact['average_tariff_reduction']
                    }
                )
                
            else:
                self.log_result(
                    "Statistics", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Statistics", 
                False, 
                f"Erreur lors de la récupération des statistiques: {str(e)}",
                {'error': str(e)}
            )

    # ==========================================
    # TESTS MODULE PRODUCTION AFRICAINE
    # ==========================================
    
    def test_production_statistics(self):
        """Test GET /api/production/statistics - Statistiques globales production"""
        try:
            response = self.session.get(f"{self.base_url}/production/statistics", timeout=TIMEOUT)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = ['total_countries', 'countries_list', 'years_covered', 'dimensions']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    self.log_result(
                        "Production Statistics", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'stats': stats}
                    )
                    return
                
                # Vérifier les valeurs attendues
                if stats['total_countries'] != 10:
                    self.log_result(
                        "Production Statistics", 
                        False, 
                        f"Nombre de pays incorrect: {stats['total_countries']} au lieu de 10",
                        {'total_countries': stats['total_countries']}
                    )
                    return
                
                # Vérifier les pays pilotes
                expected_countries = ['ZAF', 'NGA', 'EGY', 'KEN', 'GHA', 'ETH', 'CIV', 'TZA', 'MAR', 'SEN']
                if not all(country in stats['countries_list'] for country in expected_countries):
                    self.log_result(
                        "Production Statistics", 
                        False, 
                        f"Pays pilotes manquants dans la liste",
                        {'countries_list': stats['countries_list'], 'expected': expected_countries}
                    )
                    return
                
                # Vérifier les années (2021-2024)
                expected_years = [2021, 2022, 2023, 2024]
                if not all(year in stats['years_covered'] for year in expected_years):
                    self.log_result(
                        "Production Statistics", 
                        False, 
                        f"Années manquantes: attendu {expected_years}",
                        {'years_covered': stats['years_covered']}
                    )
                    return
                
                # Vérifier les 4 dimensions
                if stats['dimensions'] != 4:
                    self.log_result(
                        "Production Statistics", 
                        False, 
                        f"Nombre de dimensions incorrect: {stats['dimensions']} au lieu de 4",
                        {'dimensions': stats['dimensions']}
                    )
                    return
                
                self.log_result(
                    "Production Statistics", 
                    True, 
                    f"Statistiques production validées - {stats['total_countries']} pays, {stats['dimensions']} dimensions, années {min(stats['years_covered'])}-{max(stats['years_covered'])}",
                    {
                        'countries': stats['total_countries'],
                        'dimensions': stats['dimensions'],
                        'years': f"{min(stats['years_covered'])}-{max(stats['years_covered'])}",
                        'pilot_countries': stats['countries_list']
                    }
                )
                
            else:
                self.log_result(
                    "Production Statistics", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Production Statistics", 
                False, 
                f"Erreur lors de la récupération des statistiques production: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_macro(self):
        """Test GET /api/production/macro - Production macro-économique"""
        try:
            # Test sans paramètres
            response = self.session.get(f"{self.base_url}/production/macro", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result(
                        "Production Macro", 
                        False, 
                        "La réponse n'est pas une liste",
                        {'response_type': type(data).__name__}
                    )
                    return
                
                if len(data) == 0:
                    self.log_result(
                        "Production Macro", 
                        False, 
                        "Aucune donnée macro retournée",
                        {'data_length': len(data)}
                    )
                    return
                
                # Vérifier la structure des données
                sample_record = data[0]
                required_fields = ['country_iso3', 'year', 'sector', 'value', 'sector_detail', 'indicator_label', 'unit', 'source']
                missing_fields = [field for field in required_fields if field not in sample_record]
                
                if missing_fields:
                    self.log_result(
                        "Production Macro", 
                        False, 
                        f"Champs manquants dans les enregistrements: {missing_fields}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier les valeurs
                if sample_record['value'] <= 0:
                    self.log_result(
                        "Production Macro", 
                        False, 
                        f"Valeur invalide: {sample_record['value']}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier l'unité (percent)
                if sample_record['unit'] != 'percent':
                    self.log_result(
                        "Production Macro", 
                        False, 
                        f"Unité incorrecte: {sample_record['unit']} au lieu de 'percent'",
                        {'unit': sample_record['unit']}
                    )
                    return
                
                # Vérifier la source (World Bank)
                if 'World Bank' not in sample_record['source']:
                    self.log_result(
                        "Production Macro", 
                        False, 
                        f"Source incorrecte: {sample_record['source']}",
                        {'source': sample_record['source']}
                    )
                    return
                
                self.log_result(
                    "Production Macro", 
                    True, 
                    f"Données macro validées - {len(data)} enregistrements avec valeurs ajoutées sectorielles",
                    {
                        'records_count': len(data),
                        'sample_country': sample_record['country_iso3'],
                        'sample_sector': sample_record['sector'],
                        'sample_value': sample_record['value'],
                        'unit': sample_record['unit']
                    }
                )
                
            else:
                self.log_result(
                    "Production Macro", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Production Macro", 
                False, 
                f"Erreur lors de la récupération des données macro: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_macro_country(self):
        """Test GET /api/production/macro/{country_iso3} - Données macro par pays"""
        test_country = 'ZAF'  # Afrique du Sud
        
        try:
            response = self.session.get(f"{self.base_url}/production/macro/{test_country}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure
                required_fields = ['country_iso3', 'data_by_sector']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        f"Production Macro {test_country}", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier que c'est le bon pays
                if data['country_iso3'] != test_country:
                    self.log_result(
                        f"Production Macro {test_country}", 
                        False, 
                        f"Pays incorrect: {data['country_iso3']} au lieu de {test_country}",
                        {'returned_country': data['country_iso3']}
                    )
                    return
                
                # Vérifier l'organisation par secteur
                data_by_sector = data['data_by_sector']
                expected_sectors = ['Agriculture', 'Industry', 'Manufacturing']
                
                if not isinstance(data_by_sector, dict):
                    self.log_result(
                        f"Production Macro {test_country}", 
                        False, 
                        "data_by_sector n'est pas un dictionnaire",
                        {'data_by_sector_type': type(data_by_sector).__name__}
                    )
                    return
                
                # Vérifier qu'au moins un secteur est présent
                if len(data_by_sector) == 0:
                    self.log_result(
                        f"Production Macro {test_country}", 
                        False, 
                        "Aucune donnée sectorielle trouvée",
                        {'data_by_sector': data_by_sector}
                    )
                    return
                
                self.log_result(
                    f"Production Macro {test_country}", 
                    True, 
                    f"Données macro {test_country} organisées par secteur - {len(data_by_sector)} secteurs",
                    {
                        'country': data['country_iso3'],
                        'sectors_count': len(data_by_sector),
                        'sectors': list(data_by_sector.keys())
                    }
                )
                
            else:
                self.log_result(
                    f"Production Macro {test_country}", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Production Macro {test_country}", 
                False, 
                f"Erreur lors de la récupération des données macro {test_country}: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_agriculture(self):
        """Test GET /api/production/agriculture - Production agricole"""
        try:
            response = self.session.get(f"{self.base_url}/production/agriculture", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        "La réponse n'est pas une liste",
                        {'response_type': type(data).__name__}
                    )
                    return
                
                if len(data) == 0:
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        "Aucune donnée agricole retournée",
                        {'data_length': len(data)}
                    )
                    return
                
                # Vérifier la structure des données
                sample_record = data[0]
                required_fields = ['country_iso3', 'year', 'commodity', 'value', 'commodity_label', 'unit', 'source']
                missing_fields = [field for field in required_fields if field not in sample_record]
                
                if missing_fields:
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        f"Champs manquants dans les enregistrements: {missing_fields}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier les valeurs
                if sample_record['value'] <= 0:
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        f"Valeur invalide: {sample_record['value']}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier l'unité (tonnes)
                if sample_record['unit'] != 'tonnes':
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        f"Unité incorrecte: {sample_record['unit']} au lieu de 'tonnes'",
                        {'unit': sample_record['unit']}
                    )
                    return
                
                # Vérifier la source (FAO)
                if 'FAO' not in sample_record['source']:
                    self.log_result(
                        "Production Agriculture", 
                        False, 
                        f"Source incorrecte: {sample_record['source']}",
                        {'source': sample_record['source']}
                    )
                    return
                
                self.log_result(
                    "Production Agriculture", 
                    True, 
                    f"Données agricoles validées - {len(data)} enregistrements avec productions par culture",
                    {
                        'records_count': len(data),
                        'sample_country': sample_record['country_iso3'],
                        'sample_commodity': sample_record['commodity'],
                        'sample_value': sample_record['value'],
                        'unit': sample_record['unit']
                    }
                )
                
            else:
                self.log_result(
                    "Production Agriculture", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Production Agriculture", 
                False, 
                f"Erreur lors de la récupération des données agricoles: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_agriculture_country(self):
        """Test GET /api/production/agriculture/{country_iso3} - Données agricoles par pays"""
        test_country = 'ZAF'  # Afrique du Sud
        
        try:
            response = self.session.get(f"{self.base_url}/production/agriculture/{test_country}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure
                required_fields = ['country_iso3', 'data_by_commodity']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        f"Production Agriculture {test_country}", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier que c'est le bon pays
                if data['country_iso3'] != test_country:
                    self.log_result(
                        f"Production Agriculture {test_country}", 
                        False, 
                        f"Pays incorrect: {data['country_iso3']} au lieu de {test_country}",
                        {'returned_country': data['country_iso3']}
                    )
                    return
                
                # Vérifier l'organisation par culture
                data_by_commodity = data['data_by_commodity']
                
                if not isinstance(data_by_commodity, dict):
                    self.log_result(
                        f"Production Agriculture {test_country}", 
                        False, 
                        "data_by_commodity n'est pas un dictionnaire",
                        {'data_by_commodity_type': type(data_by_commodity).__name__}
                    )
                    return
                
                # Vérifier qu'au moins une culture est présente
                if len(data_by_commodity) == 0:
                    self.log_result(
                        f"Production Agriculture {test_country}", 
                        False, 
                        "Aucune donnée de culture trouvée",
                        {'data_by_commodity': data_by_commodity}
                    )
                    return
                
                self.log_result(
                    f"Production Agriculture {test_country}", 
                    True, 
                    f"Données agricoles {test_country} organisées par culture - {len(data_by_commodity)} cultures",
                    {
                        'country': data['country_iso3'],
                        'commodities_count': len(data_by_commodity),
                        'commodities': list(data_by_commodity.keys())
                    }
                )
                
            else:
                self.log_result(
                    f"Production Agriculture {test_country}", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Production Agriculture {test_country}", 
                False, 
                f"Erreur lors de la récupération des données agricoles {test_country}: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_manufacturing(self):
        """Test GET /api/production/manufacturing - Production manufacturière"""
        try:
            response = self.session.get(f"{self.base_url}/production/manufacturing", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        "La réponse n'est pas une liste",
                        {'response_type': type(data).__name__}
                    )
                    return
                
                if len(data) == 0:
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        "Aucune donnée manufacturière retournée",
                        {'data_length': len(data)}
                    )
                    return
                
                # Vérifier la structure des données
                sample_record = data[0]
                required_fields = ['country_iso3', 'year', 'isic_code', 'value', 'isic_label', 'unit', 'source']
                missing_fields = [field for field in required_fields if field not in sample_record]
                
                if missing_fields:
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        f"Champs manquants dans les enregistrements: {missing_fields}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier les valeurs
                if sample_record['value'] <= 0:
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        f"Valeur invalide: {sample_record['value']}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier l'unité (USD)
                if sample_record['unit'] != 'USD':
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        f"Unité incorrecte: {sample_record['unit']} au lieu de 'USD'",
                        {'unit': sample_record['unit']}
                    )
                    return
                
                # Vérifier la source (UNIDO)
                if 'UNIDO' not in sample_record['source']:
                    self.log_result(
                        "Production Manufacturing", 
                        False, 
                        f"Source incorrecte: {sample_record['source']}",
                        {'source': sample_record['source']}
                    )
                    return
                
                self.log_result(
                    "Production Manufacturing", 
                    True, 
                    f"Données manufacturières validées - {len(data)} enregistrements avec valeurs ajoutées ISIC",
                    {
                        'records_count': len(data),
                        'sample_country': sample_record['country_iso3'],
                        'sample_isic': sample_record['isic_code'],
                        'sample_value': sample_record['value'],
                        'unit': sample_record['unit']
                    }
                )
                
            else:
                self.log_result(
                    "Production Manufacturing", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Production Manufacturing", 
                False, 
                f"Erreur lors de la récupération des données manufacturières: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_manufacturing_country(self):
        """Test GET /api/production/manufacturing/{country_iso3} - Données manufacturières par pays"""
        test_country = 'ZAF'  # Afrique du Sud
        
        try:
            response = self.session.get(f"{self.base_url}/production/manufacturing/{test_country}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure
                required_fields = ['country_iso3', 'data_by_isic']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        f"Production Manufacturing {test_country}", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier que c'est le bon pays
                if data['country_iso3'] != test_country:
                    self.log_result(
                        f"Production Manufacturing {test_country}", 
                        False, 
                        f"Pays incorrect: {data['country_iso3']} au lieu de {test_country}",
                        {'returned_country': data['country_iso3']}
                    )
                    return
                
                # Vérifier l'organisation par secteur ISIC
                data_by_isic = data['data_by_isic']
                
                if not isinstance(data_by_isic, dict):
                    self.log_result(
                        f"Production Manufacturing {test_country}", 
                        False, 
                        "data_by_isic n'est pas un dictionnaire",
                        {'data_by_isic_type': type(data_by_isic).__name__}
                    )
                    return
                
                # Vérifier qu'au moins un secteur ISIC est présent
                if len(data_by_isic) == 0:
                    self.log_result(
                        f"Production Manufacturing {test_country}", 
                        False, 
                        "Aucune donnée ISIC trouvée",
                        {'data_by_isic': data_by_isic}
                    )
                    return
                
                self.log_result(
                    f"Production Manufacturing {test_country}", 
                    True, 
                    f"Données manufacturières {test_country} organisées par secteur ISIC - {len(data_by_isic)} secteurs",
                    {
                        'country': data['country_iso3'],
                        'isic_sectors_count': len(data_by_isic),
                        'isic_sectors': list(data_by_isic.keys())
                    }
                )
                
            else:
                self.log_result(
                    f"Production Manufacturing {test_country}", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Production Manufacturing {test_country}", 
                False, 
                f"Erreur lors de la récupération des données manufacturières {test_country}: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_mining(self):
        """Test GET /api/production/mining - Production minière"""
        try:
            response = self.session.get(f"{self.base_url}/production/mining", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result(
                        "Production Mining", 
                        False, 
                        "La réponse n'est pas une liste",
                        {'response_type': type(data).__name__}
                    )
                    return
                
                if len(data) == 0:
                    self.log_result(
                        "Production Mining", 
                        False, 
                        "Aucune donnée minière retournée",
                        {'data_length': len(data)}
                    )
                    return
                
                # Vérifier la structure des données
                sample_record = data[0]
                required_fields = ['country_iso3', 'year', 'commodity', 'value', 'commodity_label', 'unit', 'source']
                missing_fields = [field for field in required_fields if field not in sample_record]
                
                if missing_fields:
                    self.log_result(
                        "Production Mining", 
                        False, 
                        f"Champs manquants dans les enregistrements: {missing_fields}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier les valeurs
                if sample_record['value'] <= 0:
                    self.log_result(
                        "Production Mining", 
                        False, 
                        f"Valeur invalide: {sample_record['value']}",
                        {'sample_record': sample_record}
                    )
                    return
                
                # Vérifier l'unité (kg)
                if sample_record['unit'] != 'kg':
                    self.log_result(
                        "Production Mining", 
                        False, 
                        f"Unité incorrecte: {sample_record['unit']} au lieu de 'kg'",
                        {'unit': sample_record['unit']}
                    )
                    return
                
                # Vérifier la source (USGS)
                if 'USGS' not in sample_record['source']:
                    self.log_result(
                        "Production Mining", 
                        False, 
                        f"Source incorrecte: {sample_record['source']}",
                        {'source': sample_record['source']}
                    )
                    return
                
                self.log_result(
                    "Production Mining", 
                    True, 
                    f"Données minières validées - {len(data)} enregistrements avec productions par minerai",
                    {
                        'records_count': len(data),
                        'sample_country': sample_record['country_iso3'],
                        'sample_commodity': sample_record['commodity'],
                        'sample_value': sample_record['value'],
                        'unit': sample_record['unit']
                    }
                )
                
            else:
                self.log_result(
                    "Production Mining", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Production Mining", 
                False, 
                f"Erreur lors de la récupération des données minières: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_mining_country(self):
        """Test GET /api/production/mining/{country_iso3} - Données minières par pays"""
        test_country = 'ZAF'  # Afrique du Sud
        
        try:
            response = self.session.get(f"{self.base_url}/production/mining/{test_country}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure
                required_fields = ['country_iso3', 'data_by_commodity']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        f"Production Mining {test_country}", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier que c'est le bon pays
                if data['country_iso3'] != test_country:
                    self.log_result(
                        f"Production Mining {test_country}", 
                        False, 
                        f"Pays incorrect: {data['country_iso3']} au lieu de {test_country}",
                        {'returned_country': data['country_iso3']}
                    )
                    return
                
                # Vérifier l'organisation par minerai
                data_by_commodity = data['data_by_commodity']
                
                if not isinstance(data_by_commodity, dict):
                    self.log_result(
                        f"Production Mining {test_country}", 
                        False, 
                        "data_by_commodity n'est pas un dictionnaire",
                        {'data_by_commodity_type': type(data_by_commodity).__name__}
                    )
                    return
                
                # Vérifier qu'au moins un minerai est présent
                if len(data_by_commodity) == 0:
                    self.log_result(
                        f"Production Mining {test_country}", 
                        False, 
                        "Aucune donnée de minerai trouvée",
                        {'data_by_commodity': data_by_commodity}
                    )
                    return
                
                self.log_result(
                    f"Production Mining {test_country}", 
                    True, 
                    f"Données minières {test_country} organisées par minerai - {len(data_by_commodity)} minerais",
                    {
                        'country': data['country_iso3'],
                        'commodities_count': len(data_by_commodity),
                        'commodities': list(data_by_commodity.keys())
                    }
                )
                
            else:
                self.log_result(
                    f"Production Mining {test_country}", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Production Mining {test_country}", 
                False, 
                f"Erreur lors de la récupération des données minières {test_country}: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_overview_country(self):
        """Test GET /api/production/overview/{country_iso3} - Vue complète toutes dimensions"""
        test_country = 'ZAF'  # Afrique du Sud
        
        try:
            response = self.session.get(f"{self.base_url}/production/overview/{test_country}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure
                required_fields = ['country_iso3', 'value_added', 'agriculture', 'manufacturing', 'mining']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        f"Production Overview {test_country}", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier que c'est le bon pays
                if data['country_iso3'] != test_country:
                    self.log_result(
                        f"Production Overview {test_country}", 
                        False, 
                        f"Pays incorrect: {data['country_iso3']} au lieu de {test_country}",
                        {'returned_country': data['country_iso3']}
                    )
                    return
                
                # Vérifier que chaque dimension contient des données
                dimensions = ['value_added', 'agriculture', 'manufacturing', 'mining']
                for dimension in dimensions:
                    if dimension not in data or not data[dimension]:
                        self.log_result(
                            f"Production Overview {test_country}", 
                            False, 
                            f"Dimension {dimension} manquante ou vide",
                            {dimension: data.get(dimension)}
                        )
                        return
                
                # Compter le total des enregistrements
                total_records = 0
                for dimension in dimensions:
                    if isinstance(data[dimension], list):
                        total_records += len(data[dimension])
                    elif isinstance(data[dimension], dict):
                        total_records += sum(len(v) if isinstance(v, list) else 1 for v in data[dimension].values())
                
                self.log_result(
                    f"Production Overview {test_country}", 
                    True, 
                    f"Vue complète {test_country} validée - 4 dimensions avec {total_records} enregistrements totaux",
                    {
                        'country': data['country_iso3'],
                        'dimensions': len(dimensions),
                        'total_records': total_records,
                        'value_added_count': len(data['value_added']) if isinstance(data['value_added'], list) else 'dict',
                        'agriculture_count': len(data['agriculture']) if isinstance(data['agriculture'], list) else 'dict',
                        'manufacturing_count': len(data['manufacturing']) if isinstance(data['manufacturing'], list) else 'dict',
                        'mining_count': len(data['mining']) if isinstance(data['mining'], list) else 'dict'
                    }
                )
                
            else:
                self.log_result(
                    f"Production Overview {test_country}", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Production Overview {test_country}", 
                False, 
                f"Erreur lors de la récupération de la vue complète {test_country}: {str(e)}",
                {'error': str(e)}
            )
    
    def test_production_filtering(self):
        """Test du filtrage des données de production"""
        # Test filtrage par pays
        try:
            response = self.session.get(f"{self.base_url}/production/macro?country_iso3=ZAF", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que tous les enregistrements sont pour ZAF
                if not all(record['country_iso3'] == 'ZAF' for record in data):
                    self.log_result(
                        "Production Filtering Country", 
                        False, 
                        "Le filtrage par pays ne fonctionne pas correctement",
                        {'sample_countries': [record['country_iso3'] for record in data[:5]]}
                    )
                    return
                
                self.log_result(
                    "Production Filtering Country", 
                    True, 
                    f"Filtrage par pays ZAF validé - {len(data)} enregistrements",
                    {'filtered_records': len(data), 'country': 'ZAF'}
                )
            else:
                self.log_result(
                    "Production Filtering Country", 
                    False, 
                    f"Erreur filtrage pays: {response.status_code}",
                    {'status_code': response.status_code}
                )
        except Exception as e:
            self.log_result(
                "Production Filtering Country", 
                False, 
                f"Erreur test filtrage pays: {str(e)}",
                {'error': str(e)}
            )
        
        # Test filtrage par année
        try:
            response = self.session.get(f"{self.base_url}/production/macro?year=2024", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que tous les enregistrements sont pour 2024
                if not all(record['year'] == 2024 for record in data):
                    self.log_result(
                        "Production Filtering Year", 
                        False, 
                        "Le filtrage par année ne fonctionne pas correctement",
                        {'sample_years': [record['year'] for record in data[:5]]}
                    )
                    return
                
                self.log_result(
                    "Production Filtering Year", 
                    True, 
                    f"Filtrage par année 2024 validé - {len(data)} enregistrements",
                    {'filtered_records': len(data), 'year': 2024}
                )
            else:
                self.log_result(
                    "Production Filtering Year", 
                    False, 
                    f"Erreur filtrage année: {response.status_code}",
                    {'status_code': response.status_code}
                )
        except Exception as e:
            self.log_result(
                "Production Filtering Year", 
                False, 
                f"Erreur test filtrage année: {str(e)}",
                {'error': str(e)}
            )
        
        # Test filtrage agriculture par commodity
        try:
            response = self.session.get(f"{self.base_url}/production/agriculture?commodity=Maize", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que tous les enregistrements sont pour Maize
                if not all('Maize' in record.get('commodity_label', '') for record in data):
                    self.log_result(
                        "Production Filtering Commodity", 
                        False, 
                        "Le filtrage par commodity ne fonctionne pas correctement",
                        {'sample_commodities': [record.get('commodity_label', '') for record in data[:5]]}
                    )
                    return
                
                self.log_result(
                    "Production Filtering Commodity", 
                    True, 
                    f"Filtrage par commodity Maize validé - {len(data)} enregistrements",
                    {'filtered_records': len(data), 'commodity': 'Maize'}
                )
            else:
                self.log_result(
                    "Production Filtering Commodity", 
                    False, 
                    f"Erreur filtrage commodity: {response.status_code}",
                    {'status_code': response.status_code}
                )
        except Exception as e:
            self.log_result(
                "Production Filtering Commodity", 
                False, 
                f"Erreur test filtrage commodity: {str(e)}",
                {'error': str(e)}
            )
    
    def test_country_profile_algeria_ongoing_projects_infrastructure(self):
        """Test spécifique du profil Algérie - Vérification ongoing_projects et infrastructure_ranking selon review request"""
        country_code = 'DZ'  # Algeria
        
        try:
            response = self.session.get(f"{self.base_url}/country-profile/{country_code}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                profile = response.json()
                
                # Vérifier les champs obligatoires de base
                required_fields = ['country_code', 'country_name', 'ongoing_projects', 'infrastructure_ranking']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if missing_fields:
                    self.log_result(
                        f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'profile_keys': list(profile.keys())}
                    )
                    return
                
                # Vérifier ongoing_projects
                ongoing_projects = profile.get('ongoing_projects', [])
                if not isinstance(ongoing_projects, list):
                    self.log_result(
                        f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"ongoing_projects n'est pas une liste: {type(ongoing_projects)}",
                        {'ongoing_projects': ongoing_projects}
                    )
                    return
                
                # Vérifier infrastructure_ranking
                infrastructure_ranking = profile.get('infrastructure_ranking', {})
                if not isinstance(infrastructure_ranking, dict):
                    self.log_result(
                        f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"infrastructure_ranking n'est pas un dictionnaire: {type(infrastructure_ranking)}",
                        {'infrastructure_ranking': infrastructure_ranking}
                    )
                    return
                
                # Vérifier le contenu des projets en cours
                projects_valid = True
                projects_details = {}
                
                if len(ongoing_projects) > 0:
                    sample_project = ongoing_projects[0]
                    expected_project_fields = ['name', 'description', 'status', 'budget_usd', 'start_date']
                    missing_project_fields = [field for field in expected_project_fields if field not in sample_project]
                    
                    if missing_project_fields:
                        projects_valid = False
                        projects_details = {
                            'missing_fields': missing_project_fields,
                            'sample_project': sample_project
                        }
                    else:
                        projects_details = {
                            'count': len(ongoing_projects),
                            'sample_project_name': sample_project.get('name'),
                            'sample_budget': sample_project.get('budget_usd')
                        }
                else:
                    projects_details = {'count': 0, 'note': 'Aucun projet en cours'}
                
                # Vérifier le contenu du classement infrastructure
                ranking_valid = True
                ranking_details = {}
                
                if infrastructure_ranking:
                    expected_ranking_fields = ['africa_rank', 'global_rank', 'score', 'index_name']
                    available_ranking_fields = [field for field in expected_ranking_fields if field in infrastructure_ranking]
                    
                    if len(available_ranking_fields) > 0:
                        ranking_details = {
                            'available_fields': available_ranking_fields,
                            'africa_rank': infrastructure_ranking.get('africa_rank'),
                            'global_rank': infrastructure_ranking.get('global_rank'),
                            'score': infrastructure_ranking.get('score')
                        }
                    else:
                        ranking_valid = False
                        ranking_details = {
                            'error': 'Aucun champ de classement infrastructure trouvé',
                            'available_keys': list(infrastructure_ranking.keys())
                        }
                else:
                    ranking_details = {'note': 'Données de classement infrastructure vides'}
                
                # Résultat final
                if projects_valid and ranking_valid:
                    self.log_result(
                        f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                        True, 
                        f"✅ Algérie: ongoing_projects ({len(ongoing_projects)} projets) et infrastructure_ranking présents et valides",
                        {
                            'country': profile.get('country_name'),
                            'projects': projects_details,
                            'infrastructure_ranking': ranking_details
                        }
                    )
                else:
                    self.log_result(
                        f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"Problèmes de validation - Projects valid: {projects_valid}, Ranking valid: {ranking_valid}",
                        {
                            'projects': projects_details,
                            'infrastructure_ranking': ranking_details
                        }
                    )
                    
            else:
                self.log_result(
                    f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Algeria Profile - ongoing_projects & infrastructure_ranking", 
                False, 
                f"Erreur lors de la récupération du profil Algérie: {str(e)}",
                {'error': str(e)}
            )

    def test_country_profile_egypt_ongoing_projects_infrastructure(self):
        """Test spécifique du profil Égypte - Vérification ongoing_projects et infrastructure_ranking selon review request"""
        country_code = 'EG'  # Egypt
        
        try:
            response = self.session.get(f"{self.base_url}/country-profile/{country_code}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                profile = response.json()
                
                # Vérifier les champs obligatoires de base
                required_fields = ['country_code', 'country_name', 'ongoing_projects', 'infrastructure_ranking']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if missing_fields:
                    self.log_result(
                        f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'profile_keys': list(profile.keys())}
                    )
                    return
                
                # Vérifier ongoing_projects
                ongoing_projects = profile.get('ongoing_projects', [])
                if not isinstance(ongoing_projects, list):
                    self.log_result(
                        f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"ongoing_projects n'est pas une liste: {type(ongoing_projects)}",
                        {'ongoing_projects': ongoing_projects}
                    )
                    return
                
                # Vérifier infrastructure_ranking
                infrastructure_ranking = profile.get('infrastructure_ranking', {})
                if not isinstance(infrastructure_ranking, dict):
                    self.log_result(
                        f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"infrastructure_ranking n'est pas un dictionnaire: {type(infrastructure_ranking)}",
                        {'infrastructure_ranking': infrastructure_ranking}
                    )
                    return
                
                # Vérifier le contenu des projets en cours
                projects_valid = True
                projects_details = {}
                
                if len(ongoing_projects) > 0:
                    sample_project = ongoing_projects[0]
                    expected_project_fields = ['name', 'description', 'status', 'budget_usd', 'start_date']
                    missing_project_fields = [field for field in expected_project_fields if field not in sample_project]
                    
                    if missing_project_fields:
                        projects_valid = False
                        projects_details = {
                            'missing_fields': missing_project_fields,
                            'sample_project': sample_project
                        }
                    else:
                        projects_details = {
                            'count': len(ongoing_projects),
                            'sample_project_name': sample_project.get('name'),
                            'sample_budget': sample_project.get('budget_usd')
                        }
                else:
                    projects_details = {'count': 0, 'note': 'Aucun projet en cours'}
                
                # Vérifier le contenu du classement infrastructure
                ranking_valid = True
                ranking_details = {}
                
                if infrastructure_ranking:
                    expected_ranking_fields = ['africa_rank', 'global_rank', 'score', 'index_name']
                    available_ranking_fields = [field for field in expected_ranking_fields if field in infrastructure_ranking]
                    
                    if len(available_ranking_fields) > 0:
                        ranking_details = {
                            'available_fields': available_ranking_fields,
                            'africa_rank': infrastructure_ranking.get('africa_rank'),
                            'global_rank': infrastructure_ranking.get('global_rank'),
                            'score': infrastructure_ranking.get('score')
                        }
                    else:
                        ranking_valid = False
                        ranking_details = {
                            'error': 'Aucun champ de classement infrastructure trouvé',
                            'available_keys': list(infrastructure_ranking.keys())
                        }
                else:
                    ranking_details = {'note': 'Données de classement infrastructure vides'}
                
                # Résultat final
                if projects_valid and ranking_valid:
                    self.log_result(
                        f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                        True, 
                        f"✅ Égypte: ongoing_projects ({len(ongoing_projects)} projets) et infrastructure_ranking présents et valides",
                        {
                            'country': profile.get('country_name'),
                            'projects': projects_details,
                            'infrastructure_ranking': ranking_details
                        }
                    )
                else:
                    self.log_result(
                        f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                        False, 
                        f"Problèmes de validation - Projects valid: {projects_valid}, Ranking valid: {ranking_valid}",
                        {
                            'projects': projects_details,
                            'infrastructure_ranking': ranking_details
                        }
                    )
                    
            else:
                self.log_result(
                    f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                f"Egypt Profile - ongoing_projects & infrastructure_ranking", 
                False, 
                f"Erreur lors de la récupération du profil Égypte: {str(e)}",
                {'error': str(e)}
            )

    def test_tanger_med_port_performance_metrics_authority(self):
        """Test spécifique du Port de Tanger Med - Vérification performance metrics et authority details selon review request"""
        
        try:
            # D'abord, récupérer la liste des ports pour trouver Tanger Med
            response = self.session.get(f"{self.base_url}/logistics/ports?country_iso=MAR", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result(
                    "Tanger Med Port - Performance & Authority", 
                    False, 
                    f"Impossible de récupérer la liste des ports marocains: {response.status_code}",
                    {'status_code': response.status_code}
                )
                return
            
            ports_data = response.json()
            ports = ports_data.get('ports', [])
            
            # Chercher le port de Tanger Med
            tanger_med_port = None
            for port in ports:
                if 'tanger' in port.get('port_name', '').lower() and 'med' in port.get('port_name', '').lower():
                    tanger_med_port = port
                    break
            
            if not tanger_med_port:
                self.log_result(
                    "Tanger Med Port - Performance & Authority", 
                    False, 
                    "Port de Tanger Med non trouvé dans la liste des ports marocains",
                    {'available_ports': [p.get('port_name') for p in ports]}
                )
                return
            
            port_id = tanger_med_port.get('port_id')
            if not port_id:
                self.log_result(
                    "Tanger Med Port - Performance & Authority", 
                    False, 
                    "ID du port Tanger Med non trouvé",
                    {'tanger_med_port': tanger_med_port}
                )
                return
            
            # Récupérer les détails du port
            response = self.session.get(f"{self.base_url}/logistics/ports/{port_id}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                port_details = response.json()
                
                # Vérifier les métriques de performance
                performance_valid = True
                performance_details = {}
                
                # Chercher les métriques de performance dans différentes sections
                latest_stats = port_details.get('latest_stats', {})
                performance_metrics = port_details.get('performance_metrics', {})
                
                # Métriques attendues
                expected_performance_fields = [
                    'container_throughput_teu', 'cargo_throughput_tons', 
                    'vessel_calls', 'port_time_hours', 'waiting_time_hours',
                    'productivity_moves_per_hour', 'lsci_score'
                ]
                
                found_performance_fields = []
                performance_values = {}
                
                # Vérifier dans latest_stats
                for field in expected_performance_fields:
                    if field in latest_stats and latest_stats[field] is not None:
                        found_performance_fields.append(field)
                        performance_values[field] = latest_stats[field]
                
                # Vérifier dans performance_metrics
                for field in expected_performance_fields:
                    if field in performance_metrics and performance_metrics[field] is not None:
                        if field not in found_performance_fields:
                            found_performance_fields.append(field)
                        performance_values[field] = performance_metrics[field]
                
                if len(found_performance_fields) < 3:  # Au moins 3 métriques de performance
                    performance_valid = False
                    performance_details = {
                        'error': 'Métriques de performance insuffisantes',
                        'found_fields': found_performance_fields,
                        'expected_fields': expected_performance_fields,
                        'latest_stats': latest_stats,
                        'performance_metrics': performance_metrics
                    }
                else:
                    performance_details = {
                        'found_fields': found_performance_fields,
                        'values': performance_values,
                        'count': len(found_performance_fields)
                    }
                
                # Vérifier les détails de l'autorité portuaire
                authority_valid = True
                authority_details = {}
                
                # Chercher les informations d'autorité
                port_authority = port_details.get('port_authority', {})
                management = port_details.get('management', {})
                contact_info = port_details.get('contact_info', {})
                
                expected_authority_fields = ['name', 'type', 'website', 'contact_email', 'phone']
                found_authority_fields = []
                authority_values = {}
                
                # Vérifier dans port_authority
                for field in expected_authority_fields:
                    if field in port_authority and port_authority[field] is not None:
                        found_authority_fields.append(field)
                        authority_values[field] = port_authority[field]
                
                # Vérifier dans management
                for field in expected_authority_fields:
                    if field in management and management[field] is not None:
                        if field not in found_authority_fields:
                            found_authority_fields.append(field)
                        authority_values[field] = management[field]
                
                # Vérifier dans contact_info
                for field in expected_authority_fields:
                    if field in contact_info and contact_info[field] is not None:
                        if field not in found_authority_fields:
                            found_authority_fields.append(field)
                        authority_values[field] = contact_info[field]
                
                if len(found_authority_fields) < 2:  # Au moins 2 informations d'autorité
                    authority_valid = False
                    authority_details = {
                        'error': 'Informations d\'autorité portuaire insuffisantes',
                        'found_fields': found_authority_fields,
                        'expected_fields': expected_authority_fields,
                        'port_authority': port_authority,
                        'management': management,
                        'contact_info': contact_info
                    }
                else:
                    authority_details = {
                        'found_fields': found_authority_fields,
                        'values': authority_values,
                        'count': len(found_authority_fields)
                    }
                
                # Résultat final
                if performance_valid and authority_valid:
                    self.log_result(
                        "Tanger Med Port - Performance & Authority", 
                        True, 
                        f"✅ Port de Tanger Med: Performance metrics ({len(found_performance_fields)} métriques) et authority details ({len(found_authority_fields)} infos) présents et valides",
                        {
                            'port_name': port_details.get('port_name'),
                            'port_id': port_id,
                            'performance_metrics': performance_details,
                            'authority_details': authority_details
                        }
                    )
                else:
                    self.log_result(
                        "Tanger Med Port - Performance & Authority", 
                        False, 
                        f"Problèmes de validation - Performance valid: {performance_valid}, Authority valid: {authority_valid}",
                        {
                            'port_name': port_details.get('port_name'),
                            'performance_metrics': performance_details,
                            'authority_details': authority_details
                        }
                    )
                    
            else:
                self.log_result(
                    "Tanger Med Port - Performance & Authority", 
                    False, 
                    f"Code de statut incorrect pour les détails du port: {response.status_code}",
                    {'status_code': response.status_code, 'port_id': port_id}
                )
                
        except Exception as e:
            self.log_result(
                "Tanger Med Port - Performance & Authority", 
                False, 
                f"Erreur lors de la récupération des détails du port Tanger Med: {str(e)}",
                {'error': str(e)}
            )
    
    # ==========================================
    # TESTS MARITIME LOGISTICS CONTACTS UPDATE
    # ==========================================
    
    def test_maritime_ports_list(self):
        """Test GET /api/logistics/ports - Liste complète des 68 ports avec contacts"""
        try:
            response = self.session.get(f"{self.base_url}/logistics/ports", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de base
                if 'count' not in data or 'ports' not in data:
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        "Structure de réponse incorrecte - manque 'count' ou 'ports'",
                        {'response_keys': list(data.keys())}
                    )
                    return
                
                ports = data['ports']
                port_count = data['count']
                
                # Vérifier le nombre de ports (68 attendus)
                if port_count != 68:
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"Nombre de ports incorrect: {port_count} au lieu de 68",
                        {'actual_count': port_count}
                    )
                    return
                
                if len(ports) != 68:
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"Longueur de la liste incorrecte: {len(ports)} au lieu de 68",
                        {'actual_length': len(ports)}
                    )
                    return
                
                # Vérifier la structure des ports
                sample_port = ports[0]
                required_fields = ['port_id', 'port_name', 'country_iso', 'country_name', 'port_authority']
                missing_fields = [field for field in required_fields if field not in sample_port]
                
                if missing_fields:
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"Champs manquants dans les ports: {missing_fields}",
                        {'sample_port_keys': list(sample_port.keys())}
                    )
                    return
                
                # Vérifier la structure port_authority
                port_authority = sample_port['port_authority']
                required_authority_fields = ['name', 'address', 'website', 'contact_phone', 'contact_email']
                missing_authority_fields = [field for field in required_authority_fields if field not in port_authority]
                
                if missing_authority_fields:
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"Champs manquants dans port_authority: {missing_authority_fields}",
                        {'port_authority': port_authority}
                    )
                    return
                
                # Vérifier les formats des données
                website = port_authority['website']
                phone = port_authority['contact_phone']
                
                # Vérifier que les URLs commencent par https://
                if not website.startswith('https://'):
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"URL du site web ne commence pas par https://: {website}",
                        {'website': website}
                    )
                    return
                
                # Vérifier le format international du téléphone
                if not phone.startswith('+'):
                    self.log_result(
                        "Maritime Ports List", 
                        False, 
                        f"Numéro de téléphone pas en format international: {phone}",
                        {'phone': phone}
                    )
                    return
                
                self.log_result(
                    "Maritime Ports List", 
                    True, 
                    f"Liste des 68 ports validée avec contacts complets",
                    {
                        'total_ports': port_count,
                        'sample_port': sample_port['port_name'],
                        'sample_authority': port_authority['name'],
                        'sample_website': website,
                        'sample_phone': phone
                    }
                )
                
            else:
                self.log_result(
                    "Maritime Ports List", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Maritime Ports List", 
                False, 
                f"Erreur lors de la récupération des ports: {str(e)}",
                {'error': str(e)}
            )
    
    def test_specific_port_data_alger(self):
        """Test des données spécifiques du Port d'Alger"""
        try:
            # Chercher le port d'Alger
            response = self.session.get(f"{self.base_url}/logistics/ports?country_iso=DZA", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                ports = data['ports']
                
                # Trouver le Port d'Alger
                alger_port = None
                for port in ports:
                    if 'Alger' in port['port_name']:
                        alger_port = port
                        break
                
                if not alger_port:
                    self.log_result(
                        "Port d'Alger Specific Data", 
                        False, 
                        "Port d'Alger non trouvé dans la liste",
                        {'available_ports': [p['port_name'] for p in ports]}
                    )
                    return
                
                # Vérifier les données spécifiques
                authority = alger_port['port_authority']
                expected_phone = "+213 21 42 34 48"
                
                if authority['contact_phone'] != expected_phone:
                    self.log_result(
                        "Port d'Alger Specific Data", 
                        False, 
                        f"Téléphone incorrect: {authority['contact_phone']} au lieu de {expected_phone}",
                        {'actual_phone': authority['contact_phone'], 'expected_phone': expected_phone}
                    )
                    return
                
                # Vérifier le nom de l'autorité
                expected_authority_name = "Entreprise Portuaire d'Alger (EPAL)"
                if expected_authority_name not in authority['name']:
                    self.log_result(
                        "Port d'Alger Specific Data", 
                        False, 
                        f"Nom de l'autorité incorrect: {authority['name']}",
                        {'actual_name': authority['name'], 'expected_contains': expected_authority_name}
                    )
                    return
                
                self.log_result(
                    "Port d'Alger Specific Data", 
                    True, 
                    f"Données spécifiques du Port d'Alger validées",
                    {
                        'port_name': alger_port['port_name'],
                        'authority_name': authority['name'],
                        'phone': authority['contact_phone'],
                        'website': authority['website'],
                        'email': authority['contact_email']
                    }
                )
                
            else:
                self.log_result(
                    "Port d'Alger Specific Data", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Port d'Alger Specific Data", 
                False, 
                f"Erreur lors de la vérification du Port d'Alger: {str(e)}",
                {'error': str(e)}
            )
    
    def test_specific_port_data_tanger_med(self):
        """Test des données spécifiques du Port de Tanger Med"""
        try:
            # Chercher le port de Tanger Med
            response = self.session.get(f"{self.base_url}/logistics/ports?country_iso=MAR", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                ports = data['ports']
                
                # Trouver le Port de Tanger Med
                tanger_port = None
                for port in ports:
                    if 'Tanger Med' in port['port_name']:
                        tanger_port = port
                        break
                
                if not tanger_port:
                    self.log_result(
                        "Port de Tanger Med Specific Data", 
                        False, 
                        "Port de Tanger Med non trouvé dans la liste",
                        {'available_ports': [p['port_name'] for p in ports]}
                    )
                    return
                
                # Vérifier les données spécifiques
                authority = tanger_port['port_authority']
                expected_website = "https://www.tangermed.ma"
                
                if authority['website'] != expected_website:
                    self.log_result(
                        "Port de Tanger Med Specific Data", 
                        False, 
                        f"Site web incorrect: {authority['website']} au lieu de {expected_website}",
                        {'actual_website': authority['website'], 'expected_website': expected_website}
                    )
                    return
                
                self.log_result(
                    "Port de Tanger Med Specific Data", 
                    True, 
                    f"Données spécifiques du Port de Tanger Med validées",
                    {
                        'port_name': tanger_port['port_name'],
                        'authority_name': authority['name'],
                        'website': authority['website'],
                        'phone': authority['contact_phone'],
                        'email': authority['contact_email']
                    }
                )
                
            else:
                self.log_result(
                    "Port de Tanger Med Specific Data", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Port de Tanger Med Specific Data", 
                False, 
                f"Erreur lors de la vérification du Port de Tanger Med: {str(e)}",
                {'error': str(e)}
            )
    
    def test_specific_port_data_dakar(self):
        """Test des données spécifiques du Port de Dakar"""
        try:
            # Chercher le port de Dakar
            response = self.session.get(f"{self.base_url}/logistics/ports?country_iso=SEN", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                ports = data['ports']
                
                # Trouver le Port de Dakar
                dakar_port = None
                for port in ports:
                    if 'Dakar' in port['port_name']:
                        dakar_port = port
                        break
                
                if not dakar_port:
                    self.log_result(
                        "Port de Dakar Specific Data", 
                        False, 
                        "Port de Dakar non trouvé dans la liste",
                        {'available_ports': [p['port_name'] for p in ports]}
                    )
                    return
                
                # Vérifier les données spécifiques
                authority = dakar_port['port_authority']
                expected_authority_contains = "Port Autonome de Dakar"
                
                if expected_authority_contains not in authority['name']:
                    self.log_result(
                        "Port de Dakar Specific Data", 
                        False, 
                        f"Nom de l'autorité ne contient pas '{expected_authority_contains}': {authority['name']}",
                        {'actual_name': authority['name'], 'expected_contains': expected_authority_contains}
                    )
                    return
                
                self.log_result(
                    "Port de Dakar Specific Data", 
                    True, 
                    f"Données spécifiques du Port de Dakar validées",
                    {
                        'port_name': dakar_port['port_name'],
                        'authority_name': authority['name'],
                        'website': authority['website'],
                        'phone': authority['contact_phone'],
                        'email': authority['contact_email']
                    }
                )
                
            else:
                self.log_result(
                    "Port de Dakar Specific Data", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Port de Dakar Specific Data", 
                False, 
                f"Erreur lors de la vérification du Port de Dakar: {str(e)}",
                {'error': str(e)}
            )
    
    def test_shipping_agents_contacts(self):
        """Test des contacts des agents de transport maritime (288 agents trouvés)"""
        try:
            # Récupérer tous les ports
            response = self.session.get(f"{self.base_url}/logistics/ports", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                ports = data['ports']
                
                total_agents = 0
                agents_with_website = 0
                agents_with_phone = 0
                agents_with_email = 0
                
                # Parcourir tous les ports et compter les agents
                for port in ports:
                    if 'agents' in port:
                        port_agents = port['agents']
                        total_agents += len(port_agents)
                        
                        for agent in port_agents:
                            # Vérifier les contacts des agents
                            if 'website' in agent and agent['website'] and agent['website'] != "Non disponible":
                                agents_with_website += 1
                            
                            if 'contact' in agent and agent['contact']:
                                agents_with_phone += 1
                            
                            if 'email' in agent and agent['email']:
                                agents_with_email += 1
                
                # Vérifier le nombre total d'agents (au moins 200 attendus pour 68 ports)
                if total_agents < 200:
                    self.log_result(
                        "Shipping Agents Contacts", 
                        False, 
                        f"Nombre total d'agents trop faible: {total_agents} (attendu au moins 200 pour 68 ports)",
                        {'actual_agents': total_agents}
                    )
                    return
                
                # Vérifier que la majorité des agents ont des contacts
                website_percentage = (agents_with_website / total_agents) * 100
                phone_percentage = (agents_with_phone / total_agents) * 100
                email_percentage = (agents_with_email / total_agents) * 100
                
                if website_percentage < 50:  # Au moins 50% doivent avoir un site web
                    self.log_result(
                        "Shipping Agents Contacts", 
                        False, 
                        f"Trop peu d'agents avec site web: {website_percentage:.1f}% ({agents_with_website}/{total_agents})",
                        {'website_percentage': website_percentage}
                    )
                    return
                
                if phone_percentage < 50:  # Au moins 50% doivent avoir un téléphone
                    self.log_result(
                        "Shipping Agents Contacts", 
                        False, 
                        f"Trop peu d'agents avec téléphone: {phone_percentage:.1f}% ({agents_with_phone}/{total_agents})",
                        {'phone_percentage': phone_percentage}
                    )
                    return
                
                self.log_result(
                    "Shipping Agents Contacts", 
                    True, 
                    f"{total_agents} agents de transport validés avec contacts mis à jour",
                    {
                        'total_agents': total_agents,
                        'agents_with_website': agents_with_website,
                        'agents_with_phone': agents_with_phone,
                        'agents_with_email': agents_with_email,
                        'website_coverage': f"{website_percentage:.1f}%",
                        'phone_coverage': f"{phone_percentage:.1f}%",
                        'email_coverage': f"{email_percentage:.1f}%"
                    }
                )
                
            else:
                self.log_result(
                    "Shipping Agents Contacts", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Shipping Agents Contacts", 
                False, 
                f"Erreur lors de la vérification des agents: {str(e)}",
                {'error': str(e)}
            )
    
    def test_port_details_endpoint(self):
        """Test GET /api/logistics/ports/{port_id} - Détails d'un port spécifique"""
        try:
            # Tester avec le Port d'Alger
            port_id = "DZA-ALG-001"
            response = self.session.get(f"{self.base_url}/logistics/ports/{port_id}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                port = response.json()
                
                # Vérifier la structure complète
                required_fields = ['port_id', 'port_name', 'country_iso', 'port_authority', 'agents']
                missing_fields = [field for field in required_fields if field not in port]
                
                if missing_fields:
                    self.log_result(
                        "Port Details Endpoint", 
                        False, 
                        f"Champs manquants dans les détails du port: {missing_fields}",
                        {'port_keys': list(port.keys())}
                    )
                    return
                
                # Vérifier que c'est le bon port
                if port['port_id'] != port_id:
                    self.log_result(
                        "Port Details Endpoint", 
                        False, 
                        f"Port ID incorrect: {port['port_id']} au lieu de {port_id}",
                        {'returned_id': port['port_id']}
                    )
                    return
                
                # Vérifier les détails de l'autorité portuaire
                authority = port['port_authority']
                authority_fields = ['name', 'address', 'website', 'contact_phone', 'contact_email']
                missing_authority_fields = [field for field in authority_fields if field not in authority]
                
                if missing_authority_fields:
                    self.log_result(
                        "Port Details Endpoint", 
                        False, 
                        f"Champs manquants dans port_authority: {missing_authority_fields}",
                        {'authority_keys': list(authority.keys())}
                    )
                    return
                
                # Vérifier les agents
                agents = port['agents']
                if not isinstance(agents, list) or len(agents) == 0:
                    self.log_result(
                        "Port Details Endpoint", 
                        False, 
                        f"Agents manquants ou format incorrect: {type(agents)} avec {len(agents) if isinstance(agents, list) else 'N/A'} éléments",
                        {'agents_type': type(agents).__name__}
                    )
                    return
                
                self.log_result(
                    "Port Details Endpoint", 
                    True, 
                    f"Détails du port {port_id} validés avec autorité et {len(agents)} agents",
                    {
                        'port_id': port['port_id'],
                        'port_name': port['port_name'],
                        'authority_name': authority['name'],
                        'agents_count': len(agents),
                        'website': authority['website'],
                        'phone': authority['contact_phone']
                    }
                )
                
            elif response.status_code == 404:
                self.log_result(
                    "Port Details Endpoint", 
                    False, 
                    f"Port {port_id} non trouvé",
                    {'status_code': response.status_code}
                )
            else:
                self.log_result(
                    "Port Details Endpoint", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "Port Details Endpoint", 
                False, 
                f"Erreur lors de la récupération des détails du port: {str(e)}",
                {'error': str(e)}
            )

    # ==========================================
    # TESTS FAOSTAT ENDPOINTS
    # ==========================================
    
    def test_faostat_statistics(self):
        """Test GET /api/production/faostat/statistics"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/statistics", timeout=TIMEOUT)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Vérifier les champs obligatoires selon la demande
                required_fields = ['total_countries', 'total_commodities', 'data_year']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    self.log_result(
                        "FAOSTAT Statistics", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'stats': stats}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if stats['total_countries'] != 54:
                    self.log_result(
                        "FAOSTAT Statistics", 
                        False, 
                        f"Nombre de pays incorrect: {stats['total_countries']} au lieu de 54",
                        {'total_countries': stats['total_countries']}
                    )
                    return
                
                if stats['total_commodities'] != 47:
                    self.log_result(
                        "FAOSTAT Statistics", 
                        False, 
                        f"Nombre de commodités incorrect: {stats['total_commodities']} au lieu de 47",
                        {'total_commodities': stats['total_commodities']}
                    )
                    return
                
                if stats['data_year'] != 2023:
                    self.log_result(
                        "FAOSTAT Statistics", 
                        False, 
                        f"Année de données incorrecte: {stats['data_year']} au lieu de 2023",
                        {'data_year': stats['data_year']}
                    )
                    return
                
                self.log_result(
                    "FAOSTAT Statistics", 
                    True, 
                    f"Statistiques FAOSTAT validées - {stats['total_countries']} pays, {stats['total_commodities']} commodités, année {stats['data_year']}",
                    {
                        'total_countries': stats['total_countries'],
                        'total_commodities': stats['total_commodities'],
                        'data_year': stats['data_year']
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT Statistics", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT Statistics", 
                False, 
                f"Erreur lors de la récupération des statistiques FAOSTAT: {str(e)}",
                {'error': str(e)}
            )
    
    def test_faostat_country_civ(self):
        """Test GET /api/production/faostat/CIV - Côte d'Ivoire"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/CIV", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = ['country_name', 'region', 'main_crops']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "FAOSTAT CIV", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if data['country_name'] != "Côte d'Ivoire":
                    self.log_result(
                        "FAOSTAT CIV", 
                        False, 
                        f"Nom de pays incorrect: {data['country_name']} au lieu de 'Côte d'Ivoire'",
                        {'country_name': data['country_name']}
                    )
                    return
                
                if data['region'] != "Afrique de l'Ouest":
                    self.log_result(
                        "FAOSTAT CIV", 
                        False, 
                        f"Région incorrecte: {data['region']} au lieu de 'Afrique de l'Ouest'",
                        {'region': data['region']}
                    )
                    return
                
                # Vérifier que Cacao est dans main_crops
                if 'Cacao' not in str(data['main_crops']):
                    self.log_result(
                        "FAOSTAT CIV", 
                        False, 
                        f"Cacao manquant dans main_crops: {data['main_crops']}",
                        {'main_crops': data['main_crops']}
                    )
                    return
                
                self.log_result(
                    "FAOSTAT CIV", 
                    True, 
                    f"Données CIV validées - {data['country_name']}, région {data['region']}, Cacao présent",
                    {
                        'country_name': data['country_name'],
                        'region': data['region'],
                        'main_crops': data['main_crops']
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT CIV", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT CIV", 
                False, 
                f"Erreur lors de la récupération des données CIV: {str(e)}",
                {'error': str(e)}
            )
    
    def test_faostat_country_egy(self):
        """Test GET /api/production/faostat/EGY - Égypte"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/EGY", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = ['country_name', 'production_2023']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "FAOSTAT EGY", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if data['country_name'] != "Égypte":
                    self.log_result(
                        "FAOSTAT EGY", 
                        False, 
                        f"Nom de pays incorrect: {data['country_name']} au lieu de 'Égypte'",
                        {'country_name': data['country_name']}
                    )
                    return
                
                # Vérifier que Blé et Riz sont dans production_2023
                production_str = str(data['production_2023'])
                if 'Blé' not in production_str:
                    self.log_result(
                        "FAOSTAT EGY", 
                        False, 
                        f"Blé manquant dans production_2023: {data['production_2023']}",
                        {'production_2023': data['production_2023']}
                    )
                    return
                
                if 'Riz' not in production_str:
                    self.log_result(
                        "FAOSTAT EGY", 
                        False, 
                        f"Riz manquant dans production_2023: {data['production_2023']}",
                        {'production_2023': data['production_2023']}
                    )
                    return
                
                self.log_result(
                    "FAOSTAT EGY", 
                    True, 
                    f"Données EGY validées - {data['country_name']}, Blé et Riz présents",
                    {
                        'country_name': data['country_name'],
                        'production_2023': data['production_2023']
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT EGY", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT EGY", 
                False, 
                f"Erreur lors de la récupération des données EGY: {str(e)}",
                {'error': str(e)}
            )
    
    def test_faostat_top_producers_cacao(self):
        """Test GET /api/production/faostat/top-producers/Cacao"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/top-producers/Cacao", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient 'producers'
                if 'producers' not in data:
                    self.log_result(
                        "FAOSTAT Top Producers Cacao", 
                        False, 
                        "Champ 'producers' manquant dans la réponse",
                        {'data': data}
                    )
                    return
                
                producers = data['producers']
                if not isinstance(producers, list):
                    self.log_result(
                        "FAOSTAT Top Producers Cacao", 
                        False, 
                        "Le champ 'producers' n'est pas une liste",
                        {'producers_type': type(producers).__name__}
                    )
                    return
                
                if len(producers) == 0:
                    self.log_result(
                        "FAOSTAT Top Producers Cacao", 
                        False, 
                        "Aucun producteur de cacao retourné",
                        {'producers_length': len(producers)}
                    )
                    return
                
                # Vérifier que CIV est #1 et GHA est #2 selon la demande
                if len(producers) >= 2:
                    first_producer = producers[0]
                    second_producer = producers[1]
                    
                    if first_producer.get('country') != 'CIV':
                        self.log_result(
                            "FAOSTAT Top Producers Cacao", 
                            False, 
                            f"CIV n'est pas le premier producteur: {first_producer}",
                            {'first_producer': first_producer}
                        )
                        return
                    
                    if second_producer.get('country') != 'GHA':
                        self.log_result(
                            "FAOSTAT Top Producers Cacao", 
                            False, 
                            f"GHA n'est pas le deuxième producteur: {second_producer}",
                            {'second_producer': second_producer}
                        )
                        return
                
                self.log_result(
                    "FAOSTAT Top Producers Cacao", 
                    True, 
                    f"Classement cacao validé - {len(producers)} producteurs, CIV #1, GHA #2",
                    {
                        'producers_count': len(producers),
                        'top_2': producers[:2] if len(producers) >= 2 else producers
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT Top Producers Cacao", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT Top Producers Cacao", 
                False, 
                f"Erreur lors de la récupération du classement cacao: {str(e)}",
                {'error': str(e)}
            )
    
    def test_faostat_commodities(self):
        """Test GET /api/production/faostat/commodities"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/commodities", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient 'commodities'
                if 'commodities' not in data:
                    self.log_result(
                        "FAOSTAT Commodities", 
                        False, 
                        "Champ 'commodities' manquant dans la réponse",
                        {'data': data}
                    )
                    return
                
                commodities = data['commodities']
                if not isinstance(commodities, list):
                    self.log_result(
                        "FAOSTAT Commodities", 
                        False, 
                        "Le champ 'commodities' n'est pas une liste",
                        {'commodities_type': type(commodities).__name__}
                    )
                    return
                
                if len(commodities) == 0:
                    self.log_result(
                        "FAOSTAT Commodities", 
                        False, 
                        "Aucune commodité retournée",
                        {'commodities_length': len(commodities)}
                    )
                    return
                
                self.log_result(
                    "FAOSTAT Commodities", 
                    True, 
                    f"Liste des commodités agricoles validée - {len(commodities)} commodités",
                    {
                        'commodities_count': len(commodities),
                        'sample_commodities': commodities[:5] if len(commodities) >= 5 else commodities
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT Commodities", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT Commodities", 
                False, 
                f"Erreur lors de la récupération des commodités: {str(e)}",
                {'error': str(e)}
            )
    
    def test_faostat_fisheries(self):
        """Test GET /api/production/faostat/fisheries"""
        try:
            response = self.session.get(f"{self.base_url}/production/faostat/fisheries", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient des données de pêche
                if not data:
                    self.log_result(
                        "FAOSTAT Fisheries", 
                        False, 
                        "Aucune donnée de pêche retournée",
                        {'data': data}
                    )
                    return
                
                self.log_result(
                    "FAOSTAT Fisheries", 
                    True, 
                    "Données de pêche et aquaculture validées",
                    {
                        'fisheries_data': data
                    }
                )
                
            else:
                self.log_result(
                    "FAOSTAT Fisheries", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "FAOSTAT Fisheries", 
                False, 
                f"Erreur lors de la récupération des données de pêche: {str(e)}",
                {'error': str(e)}
            )
    
    # ==========================================
    # TESTS UNIDO ENDPOINTS
    # ==========================================
    
    def test_unido_statistics(self):
        """Test GET /api/production/unido/statistics"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/statistics", timeout=TIMEOUT)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Vérifier les champs obligatoires selon la demande
                required_fields = ['total_countries', 'total_mva_bln_usd']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    self.log_result(
                        "UNIDO Statistics", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'stats': stats}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if stats['total_countries'] != 54:
                    self.log_result(
                        "UNIDO Statistics", 
                        False, 
                        f"Nombre de pays incorrect: {stats['total_countries']} au lieu de 54",
                        {'total_countries': stats['total_countries']}
                    )
                    return
                
                # Vérifier que total_mva_bln_usd est proche de 289.9
                expected_mva = 289.9
                actual_mva = stats['total_mva_bln_usd']
                if abs(actual_mva - expected_mva) > 10:  # Tolérance de 10 milliards
                    self.log_result(
                        "UNIDO Statistics", 
                        False, 
                        f"MVA total incorrect: {actual_mva} au lieu de ~{expected_mva}",
                        {'total_mva_bln_usd': actual_mva}
                    )
                    return
                
                self.log_result(
                    "UNIDO Statistics", 
                    True, 
                    f"Statistiques UNIDO validées - {stats['total_countries']} pays, MVA total ${actual_mva}B",
                    {
                        'total_countries': stats['total_countries'],
                        'total_mva_bln_usd': actual_mva
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO Statistics", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO Statistics", 
                False, 
                f"Erreur lors de la récupération des statistiques UNIDO: {str(e)}",
                {'error': str(e)}
            )
    
    def test_unido_country_mar(self):
        """Test GET /api/production/unido/MAR - Maroc"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/MAR", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = ['country_name', 'mva_2023_mln_usd', 'mva_gdp_percent']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "UNIDO MAR", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if data['country_name'] != "Maroc":
                    self.log_result(
                        "UNIDO MAR", 
                        False, 
                        f"Nom de pays incorrect: {data['country_name']} au lieu de 'Maroc'",
                        {'country_name': data['country_name']}
                    )
                    return
                
                expected_mva = 32500
                actual_mva = data['mva_2023_mln_usd']
                if abs(actual_mva - expected_mva) > 1000:  # Tolérance de 1 milliard
                    self.log_result(
                        "UNIDO MAR", 
                        False, 
                        f"MVA 2023 incorrect: {actual_mva} au lieu de {expected_mva}",
                        {'mva_2023_mln_usd': actual_mva}
                    )
                    return
                
                expected_gdp_percent = 24.8
                actual_gdp_percent = data['mva_gdp_percent']
                if abs(actual_gdp_percent - expected_gdp_percent) > 2:  # Tolérance de 2%
                    self.log_result(
                        "UNIDO MAR", 
                        False, 
                        f"MVA/PIB incorrect: {actual_gdp_percent}% au lieu de {expected_gdp_percent}%",
                        {'mva_gdp_percent': actual_gdp_percent}
                    )
                    return
                
                self.log_result(
                    "UNIDO MAR", 
                    True, 
                    f"Données MAR validées - {data['country_name']}, MVA ${actual_mva}M, MVA/PIB {actual_gdp_percent}%",
                    {
                        'country_name': data['country_name'],
                        'mva_2023_mln_usd': actual_mva,
                        'mva_gdp_percent': actual_gdp_percent
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO MAR", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO MAR", 
                False, 
                f"Erreur lors de la récupération des données MAR: {str(e)}",
                {'error': str(e)}
            )
    
    def test_unido_country_zaf(self):
        """Test GET /api/production/unido/ZAF - Afrique du Sud"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/ZAF", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier les champs obligatoires
                required_fields = ['country_name', 'top_sectors']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "UNIDO ZAF", 
                        False, 
                        f"Champs manquants: {missing_fields}",
                        {'data': data}
                    )
                    return
                
                # Vérifier les valeurs attendues selon la demande
                if data['country_name'] != "Afrique du Sud":
                    self.log_result(
                        "UNIDO ZAF", 
                        False, 
                        f"Nom de pays incorrect: {data['country_name']} au lieu de 'Afrique du Sud'",
                        {'country_name': data['country_name']}
                    )
                    return
                
                # Vérifier que automobile est dans top_sectors
                top_sectors_str = str(data['top_sectors'])
                if 'automobile' not in top_sectors_str.lower():
                    self.log_result(
                        "UNIDO ZAF", 
                        False, 
                        f"Automobile manquant dans top_sectors: {data['top_sectors']}",
                        {'top_sectors': data['top_sectors']}
                    )
                    return
                
                self.log_result(
                    "UNIDO ZAF", 
                    True, 
                    f"Données ZAF validées - {data['country_name']}, automobile présent dans top_sectors",
                    {
                        'country_name': data['country_name'],
                        'top_sectors': data['top_sectors']
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO ZAF", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO ZAF", 
                False, 
                f"Erreur lors de la récupération des données ZAF: {str(e)}",
                {'error': str(e)}
            )
    
    def test_unido_ranking(self):
        """Test GET /api/production/unido/ranking"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/ranking", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient 'ranking'
                if 'ranking' not in data:
                    self.log_result(
                        "UNIDO Ranking", 
                        False, 
                        "Champ 'ranking' manquant dans la réponse",
                        {'data': data}
                    )
                    return
                
                ranking = data['ranking']
                if not isinstance(ranking, list):
                    self.log_result(
                        "UNIDO Ranking", 
                        False, 
                        "Le champ 'ranking' n'est pas une liste",
                        {'ranking_type': type(ranking).__name__}
                    )
                    return
                
                if len(ranking) == 0:
                    self.log_result(
                        "UNIDO Ranking", 
                        False, 
                        "Aucun classement retourné",
                        {'ranking_length': len(ranking)}
                    )
                    return
                
                # Vérifier que ZAF, EGY, NGA sont dans le top selon la demande
                top_countries = [item.get('country_iso3', '') for item in ranking[:5]]
                expected_top = ['ZAF', 'EGY', 'NGA']
                
                for country in expected_top:
                    if country not in top_countries:
                        self.log_result(
                            "UNIDO Ranking", 
                            False, 
                            f"{country} manquant dans le top 5: {top_countries}",
                            {'top_5': top_countries}
                        )
                        return
                
                self.log_result(
                    "UNIDO Ranking", 
                    True, 
                    f"Classement MVA validé - {len(ranking)} pays, ZAF/EGY/NGA dans le top",
                    {
                        'countries_count': len(ranking),
                        'top_5': top_countries
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO Ranking", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO Ranking", 
                False, 
                f"Erreur lors de la récupération du classement: {str(e)}",
                {'error': str(e)}
            )
    
    def test_unido_sector_analysis(self):
        """Test GET /api/production/unido/sector-analysis/10"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/sector-analysis/10", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient une analyse du secteur alimentaire
                if not data:
                    self.log_result(
                        "UNIDO Sector Analysis 10", 
                        False, 
                        "Aucune analyse sectorielle retournée",
                        {'data': data}
                    )
                    return
                
                self.log_result(
                    "UNIDO Sector Analysis 10", 
                    True, 
                    "Analyse du secteur alimentaire (ISIC 10) validée",
                    {
                        'sector_analysis': data
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO Sector Analysis 10", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO Sector Analysis 10", 
                False, 
                f"Erreur lors de la récupération de l'analyse sectorielle: {str(e)}",
                {'error': str(e)}
            )
    
    def test_unido_isic_sectors(self):
        """Test GET /api/production/unido/isic-sectors"""
        try:
            response = self.session.get(f"{self.base_url}/production/unido/isic-sectors", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que la réponse contient 'sectors'
                if 'sectors' not in data:
                    self.log_result(
                        "UNIDO ISIC Sectors", 
                        False, 
                        "Champ 'sectors' manquant dans la réponse",
                        {'data': data}
                    )
                    return
                
                sectors = data['sectors']
                if not isinstance(sectors, dict):
                    self.log_result(
                        "UNIDO ISIC Sectors", 
                        False, 
                        "Le champ 'sectors' n'est pas un dictionnaire",
                        {'sectors_type': type(sectors).__name__}
                    )
                    return
                
                if len(sectors) == 0:
                    self.log_result(
                        "UNIDO ISIC Sectors", 
                        False, 
                        "Aucun secteur ISIC retourné",
                        {'sectors_length': len(sectors)}
                    )
                    return
                
                # Vérifier que les codes ISIC 10-33 sont présents selon la demande
                isic_codes = list(sectors.keys())
                expected_range = [str(i) for i in range(10, 34)]  # 10-33
                missing_codes = [code for code in expected_range if code not in isic_codes]
                
                if missing_codes:
                    self.log_result(
                        "UNIDO ISIC Sectors", 
                        False, 
                        f"Codes ISIC manquants (10-33): {missing_codes}",
                        {'isic_codes': isic_codes}
                    )
                    return
                
                self.log_result(
                    "UNIDO ISIC Sectors", 
                    True, 
                    f"Classification ISIC Rev.4 validée - {len(sectors)} secteurs, codes 10-33 présents",
                    {
                        'sectors_count': len(sectors),
                        'sample_codes': list(sectors.keys())[:10]
                    }
                )
                
            else:
                self.log_result(
                    "UNIDO ISIC Sectors", 
                    False, 
                    f"Code de statut incorrect: {response.status_code}",
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            self.log_result(
                "UNIDO ISIC Sectors", 
                False, 
                f"Erreur lors de la récupération des secteurs ISIC: {str(e)}",
                {'error': str(e)}
            )

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print(f"🚀 Début des tests de l'API ZLECAf")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Timeout: {TIMEOUT}s")
        print("=" * 80)
        
        # Exécuter tous les tests
        self.test_api_root()
        self.test_countries_list()
        self.test_country_profiles()
        self.test_rules_of_origin()
        self.test_tax_implementation_senegal_cote_ivoire()  # Test spécifique des taxes
        self.test_tariff_calculation()
        self.test_statistics()
        
        # Tests spécifiques de la review request
        print("\n" + "=" * 80)
        print("🎯 TESTS SPÉCIFIQUES REVIEW REQUEST")
        print("=" * 80)
        self.test_country_profile_algeria_ongoing_projects_infrastructure()
        self.test_country_profile_egypt_ongoing_projects_infrastructure()
        self.test_tanger_med_port_performance_metrics_authority()
        
        # Tests du module Production
        print("\n" + "=" * 80)
        print("📊 TESTS MODULE PRODUCTION")
        print("=" * 80)
        self.test_production_statistics()
        self.test_production_macro()
        self.test_production_macro_country()
        self.test_production_agriculture()
        self.test_production_agriculture_country()
        self.test_production_manufacturing()
        self.test_production_manufacturing_country()
        self.test_production_mining()
        self.test_production_mining_country()
        self.test_production_overview_country()
        self.test_production_filtering()
        
        # Tests FAOSTAT (nouveaux)
        print("\n" + "=" * 80)
        print("🌾 TESTS FAOSTAT PRODUCTION AGRICOLE")
        print("=" * 80)
        self.test_faostat_statistics()
        self.test_faostat_country_civ()
        self.test_faostat_country_egy()
        self.test_faostat_top_producers_cacao()
        self.test_faostat_commodities()
        self.test_faostat_fisheries()
        
        # Tests UNIDO (nouveaux)
        print("\n" + "=" * 80)
        print("🏭 TESTS UNIDO PRODUCTION INDUSTRIELLE")
        print("=" * 80)
        self.test_unido_statistics()
        self.test_unido_country_mar()
        self.test_unido_country_zaf()
        self.test_unido_ranking()
        self.test_unido_sector_analysis()
        self.test_unido_isic_sectors()
        
        # Tests Maritime Logistics Contacts Update
        print("\n" + "=" * 80)
        print("🚢 TESTS MARITIME LOGISTICS CONTACTS UPDATE")
        print("=" * 80)
        self.test_maritime_ports_list()
        self.test_specific_port_data_alger()
        self.test_specific_port_data_tanger_med()
        self.test_specific_port_data_dakar()
        self.test_shipping_agents_contacts()
        self.test_port_details_endpoint()
        
        # Résumé des résultats
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🔍 TESTS ÉCHOUÉS:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        return passed_tests == total_tests

def main():
    """Fonction principale"""
    tester = ZLECAfAPITester()
    success = tester.run_all_tests()
    
    # Sauvegarder les résultats détaillés
    with open('/app/test_results_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Résultats détaillés sauvegardés dans: /app/test_results_detailed.json")
    
    if success:
        print("🎉 Tous les tests ont réussi!")
        sys.exit(0)
    else:
        print("⚠️  Certains tests ont échoué. Voir les détails ci-dessus.")
        sys.exit(1)

if __name__ == "__main__":
    main()