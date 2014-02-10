USE [Khan]
GO

/****** Object:  Table [dbo].[badge_metadata]    Script Date: 02/07/2014 19:17:13 ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[badge_metadata]') AND type in (N'U'))
DROP TABLE [dbo].[badge_metadata]
GO

USE [Khan]
GO

/****** Object:  Table [dbo].[badge_metadata]    Script Date: 02/07/2014 19:17:13 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[badge_metadata](
	[icon_src] [varchar](255) NULL,
	[hide_context] [char](5) NULL,
	[description] [varchar](255) NULL,
	[absolute_url] [varchar](255) NULL,
	[translated_safe_extended_description] [varchar](255) NULL,
	[name] [varchar](255) NULL,
	[translated_description] [varchar](255) NULL,
	[icon_large] [varchar](255) NULL,
	[icon_compact] [varchar](255) NULL,
	[is_retired] [char](5) NULL,
	[icon_small] [varchar](255) NULL,
	[badge_category] [int] NULL,
	[safe_extended_description] [varchar](255) NULL,
	[slug] [varchar](255) NULL,
	[points] [int] NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO


