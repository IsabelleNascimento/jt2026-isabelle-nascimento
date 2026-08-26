# EDA — Itapema (SC)

### Tabela de Dados — Details_Itapema.csv
| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |
|--------|--------------|------------------|------------------|
| airbnb_listing_id | int64 | 0 (0.0%) | 1018938592594574382 |
| url | object | 0 (0.0%) | https://www.airbnb.com.br/rooms/1018938592594574382 |
| ad_name | object | 0 (0.0%) | Apartamento em centro itapema |
| ad_description | object | 54 (1.22%) | Aconchegante, bem iluminado, poucos metros do mar,  lugar tranquilo e bem-localizado |
| space | object | 2527 (56.9%) | <br />Para o conforto de nossos hóspedes, o imóvel possui:<br /><br />- Ambientes integrados, espaçosos e bem iluminados;<br />- 1 suíte com cama casal, ar-condicionado e armário;<br />- 1 demi-suíte com cama de casal, cômoda; ( nesse quarto tem uma porta para acesso ao banheiro social )<br />- 1 quarto com cama de casal, armário, cômoda e ar-condicionado;<br />- Sala de estar com sofá, poltrona, rack, TV, mesa de jantar com 6 lugares;<br /><br />- Varanda com churrasqueira e mesa;<br />- Cozinha completa com geladeira, fogão, micro-ondas, sanduicheira, liquidificador, chaleira elétrica, e demais utensílios;<br />- 1 banheiro social;<br />- Área de serviço com máquina de lavar e varal;<br />- Wi-fi 30mb disponível;<br />- 1 vaga de garagem coberta. (comporta caminhonete, tamanho 3x2)<br /><br /><br /><br />OBS: Informamos que há uma obra em andamento no prédio, sem previsão de término.<br /><br />* São disponibilizadas uma toalha de banho por hóspede e uma toalha de rosto por banheiro, além de lençóis para a quantidade de hóspedes indicada, trocas de enxoval podem ser solicitadas ao valor de meia taxa de limpeza.<br /><br />* A limpeza inclusa no valor é realizada somente no checkout. Se o hóspede desejar uma limpeza extra durante a estadia, será cobrada uma nova taxa de limpeza.<br /><br />IMPORTANTE: Para check-in após as 20h há cobrança adicional de taxa de conveniência, consulte valores e formas de pagamento com o anfitrião :)<br /><br />Venha, relaxe, divirta-se e não se preocupe com mais nada :)<br /><br /> |
| house_rules | object | 0 (0.0%) | ["Máximo de 4 hóspedes", "Não é permitido animais de estimação", "Horário de silêncio", "Não são permitidas festas ou eventos", "Proibido fumar"] |
| amenities | object | 0 (0.0%) | ["Chuveiro externo", "Máquina de lavar Gratuito", "Roupa de cama", "Varal para secar roupas", "Local para guardar as roupas: guarda-roupa", "HDTV", "Ar-condicionado split", "Ventilador de teto", "Wi-Fi", "Refrigerador", "Microondas", "Louças e talheres", "Fogão a gás Other", "Forno Normal", "Liquidificador", "Churrasqueira", "Estacionamento incluído", "O anfitrião recebe você"] |
| safety_features | object | 0 (0.0%) | ["Alarme de monóxido de carbono não informado", "Detector de fumaça não informado"] |
| number_of_bathrooms | float64 | 0 (0.0%) | 1.0 |
| number_of_bedrooms | int64 | 0 (0.0%) | 1 |
| number_of_beds | int64 | 0 (0.0%) | 1 |
| latitude | float64 | 0 (0.0%) | 0.0 |
| longitude | float64 | 0 (0.0%) | 0.0 |
| check_in | object | 446 (10.04%) | Check-in: 14:00 - 20:00 |
| check_out | object | 842 (18.96%) | Checkout antes das 09:00 |
| number_of_guests | int64 | 0 (0.0%) | 4 |
| number_of_reviews | int64 | 0 (0.0%) | 0 |
| cleaning_fee | float64 | 0 (0.0%) | 200.0 |
| owner_id | int64 | 0 (0.0%) | 545255849 |
| aquisition_date | object | 0 (0.0%) | 2025-01-13 02:58:38.000 |
| star_rating | float64 | 0 (0.0%) | 0.0 |
| picture_count | int64 | 0 (0.0%) | 0 |
| min_nights | int64 | 0 (0.0%) | 0 |
| guest_satisfaction_overall | int64 | 0 (0.0%) | 0 |
| listing_type | object | 0 (0.0%) | apartamento |
| can_instant_book | object | 355 (7.99%) | False |
| is_professional | object | 355 (7.99%) | False |
| accuracy_rating | float64 | 0 (0.0%) | 0.0 |
| checkin_rating | float64 | 0 (0.0%) | 0.0 |
| cleanliness_rating | float64 | 0 (0.0%) | 0.0 |
| communication_rating | float64 | 0 (0.0%) | 0.0 |
| location_rating | float64 | 0 (0.0%) | 0.0 |
| value_rating | float64 | 0 (0.0%) | 0.0 |
| is_new_listing | object | 874 (19.68%) | False |
| is_guest_favorite | bool | 0 (0.0%) | False |

### Tabela de Dados — Hosts_ids_Itapema.csv
| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |
|--------|--------------|------------------|------------------|
| owner_id | int64 | 0 (0.0%) | 167418369 |
| owner | object | 0 (0.0%) | Cristiane |
| is_superhost | bool | 0 (0.0%) | False |
| number_of_reviews_host | float64 | 0 (0.0%) | 1.0 |
| is_verified | bool | 0 (0.0%) | True |
| star_rating_host | float64 | 0 (0.0%) | 5.0 |
| years_host | int64 | 0 (0.0%) | 0 |
| months_host | int64 | 0 (0.0%) | 10 |
| response_rate_shown | float64 | 4440 (100.0%) | VAZIO |
| response_time_shown | float64 | 4440 (100.0%) | VAZIO |
| host_snapshot_date | object | 0 (0.0%) | 2025-01-13 02:25:40.000 |

### Tabela de Dados — Mesh_Ids_Data_Itapema.csv
| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |
|--------|--------------|------------------|------------------|
| airbnb_listing_id | int64 | 0 (0.0%) | 1207992119242235910 |
| latitude | float64 | 0 (0.0%) | -27.09306 |
| longitude | float64 | 0 (0.0%) | -48.61326 |
| suburb | object | 0 (0.0%) | Centro |
| country | object | 0 (0.0%) | Brasil |
| state | object | 0 (0.0%) | Santa Catarina |
| city | object | 0 (0.0%) | Itapema |
| aquisition_date | object | 0 (0.0%) | 2025-11-03 19:00:38.406 |

### Tabela de Dados — Price_AV_Itapema.csv
| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |
|--------|--------------|------------------|------------------|
| airbnb_listing_id | int64 | 0 (0.0%) | 1002785860497857801 |
| date | object | 0 (0.0%) | 2025-01-23 |
| price | float64 | 0 (0.0%) | 800.0 |
| aquisition_date | object | 0 (0.0%) | 2025-01-07 13:25:06.000 |

### Tabela de Dados — VivaReal_Itapema.csv
| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |
|--------|--------------|------------------|------------------|
| listing_id | int64 | 0 (0.0%) | 2687011752 |
| link_url | object | 0 (0.0%) | https://www.vivareal.com.br/imovel/apartamento-3-quartos-meia-praia-bairros-itapema-com-garagem-131m2-venda-RS1598122-id-2687011752/ |
| listing_title | object | 0 (0.0%) | ITAPEMA - Apartamento Padrão - Meia Praia |
| business_types | object | 0 (0.0%) | Venda |
| listing_type | object | 0 (0.0%) | apartamento |
| property_type | object | 0 (0.0%) | UNIT |
| sale_price | float64 | 0 (0.0%) | 1598122.0 |
| rental_price | float64 | 8327 (99.98%) | 15000.0 |
| rental_period | object | 8327 (99.98%) | MONTHLY |
| yearly_iptu | float64 | 2714 (32.58%) | 0.0 |
| monthly_condo_fee | float64 | 2490 (29.9%) | 350.0 |
| amenities | object | 0 (0.0%) | ["POOL", "ELEVATOR", "PLAYGROUND", "PARTY_HALL"] |
| usable_area | int64 | 0 (0.0%) | 131 |
| bathrooms | int64 | 0 (0.0%) | 4 |
| bedrooms | int64 | 0 (0.0%) | 3 |
| parking_spaces | int64 | 0 (0.0%) | 2 |
| state | object | 2 (0.02%) | SC |
| city | object | 0 (0.0%) | Itapema |
| suburb | object | 98 (1.18%) | Meia Praia |
| advertiser_name | object | 0 (0.0%) | Leonardo Batista |
| portal | object | 0 (0.0%) | GRUPOZAP |
| aquisition_date | object | 0 (0.0%) | 2025-01-11 00:00:00.000 |

