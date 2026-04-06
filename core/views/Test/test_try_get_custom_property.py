# $EwsDllPath = "C:\Users\DSvietnoi\Desktop\MyTemp\Microsoft.Exchange.WebServices.dll"
# Import-Module $EwsDllPath
# $service = New-Object Microsoft.Exchange.WebServices.Data.ExchangeService
# [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
# $service.Credentials = New-Object Microsoft.Exchange.WebServices.Data.WebCredentials("ESync@privser.com", "aa2414hbBMW#ESY")
# $service.Url = [Uri] "https://mail.privser.com/ews/exchange.asmx"
# $contact = [Microsoft.Exchange.WebServices.Data.Contact]::Bind($service, "AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAADy7w6A6MWMTKhQqDM7ARKlAAW7A0XCAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAAA=")
# $contact.ExtendedProperties | ForEach-Object {
#     Write-Output ("Property Tag: " + $_.PropertyDefinition.PropertyTag)
#     Write-Output ("Property Name: " + $_.PropertyDefinition.Name)
#     Write-Output ("Value: " + $_.Value)
# }




#    Connection successful
#    User:
# $service = New-Object Microsoft.Exchange.WebServices.Data.ExchangeService
# [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
# $service.Credentials = New-Object Microsoft.Exchange.WebServices.Data.WebCredentials("ESync@privser.com", "aa2414hbBMW#ESY")
# $service.Url = [Uri] "https://dbpserver-011.privser.com:444/EWS/Services.wsdl"
#
# try {
#     # Пытаемся получить информацию о текущем пользователе
#     $user = $service.CurrentUser
#     Write-Host "Connection successful"
#     Write-Host "User: $($user.DisplayName)"
# }
# catch {
#     Write-Host "Connection failed: $_"
# }


#
#
# [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
# curl https://mail.privser.com/ews/exchange.asmx



# Пример: создание объекта ExchangeService и получения контакта
# $EwsDllPath = "C:\Users\DSvietnoi\Desktop\MyTemp\Microsoft.Exchange.WebServices.dll"
# [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
# [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
# Import-Module $EwsDllPath
#
# # Создаем экземпляр ExchangeService
# $service = New-Object Microsoft.Exchange.WebServices.Data.ExchangeService
# $service.Credentials = New-Object Microsoft.Exchange.WebServices.Data.WebCredentials("ESync@privser.com", "aa2414hbBMW#ESY")
# $service.Url = [Uri] "https://dbpserver-011.privser.com:444/EWS/Services.wsdl"
#
# # Получаем контакт
# $contactId = "AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAADy7w6A6MWMTKhQqDM7ARKlAAW7A0XCAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAAA="
# $contact = [Microsoft.Exchange.WebServices.Data.Contact]::Bind($service, $contactId)
#
# # Доступ к свойствам с использованием FirstClassProperties
# $propertySet = [Microsoft.Exchange.WebServices.Data.PropertySet]::FirstClassProperties
# $contact.Load($propertySet)


# Загрузка EWS Managed API
# Add-Type -Path "C:\Users\DSvietnoi\Desktop\MyTemp\Microsoft.Exchange.WebServices.dll"
#
# # Создание экземпляра ExchangeService
# $service = New-Object Microsoft.Exchange.WebServices.Data.ExchangeService
# $service.Credentials = New-Object Microsoft.Exchange.WebServices.Data.WebCredentials("ESync@privser.com", "aa2414hbBMW#ESY")
# $service.Url = [Uri] "https://mail.privser.com/ews/exchange.asmx"
#
# # Получение контакта
# $contact = [Microsoft.Exchange.WebServices.Data.Contact]::Bind($service, "AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAADy7w6A6MWMTKhQqDM7ARKlAAW7A0XCAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUABbsDQacAAAA=")
#
# # Чтение расширенных свойств
# $contact.ExtendedProperties | ForEach-Object {
#     Write-Host ("Property Tag: " + $_.PropertyDefinition.PropertyTag)
#     Write-Host ("Property Set ID: " + $_.PropertyDefinition.PropertySetId)
#     Write-Host ("Property Value: " + $_.Value)
# }
